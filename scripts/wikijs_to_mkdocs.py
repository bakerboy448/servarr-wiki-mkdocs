#!/usr/bin/env python3
"""Convert WikiJS-flavored Servarr wiki markdown to MkDocs Material."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path, PurePosixPath

CALLOUT_TYPES = {
    "info": "info",
    "warning": "warning",
    "danger": "danger",
    "success": "success",
}

ICON_PREFIX = {
    "fas": "solid",
    "far": "regular",
    "fab": "brands",
    "fal": "solid",
    "fad": "solid",
}

FRONTMATTER_DROP = {"published", "date", "editor", "dateCreated"}
# Matches both legacy ("fas fa-x", "fab fa-x") and FA5+/6 ("fa-solid fa-x") forms,
# including optional style/aria attributes.
ICON_RE = re.compile(
    r'<i\s+class="'
    r'(?:'
    r'(?P<style>fa[srlbd]?)\s+fa-(?P<name>[a-z0-9-]+)'
    r'|'
    r'fa-(?P<style2>solid|regular|brands|light|duotone)\s+fa-(?P<name2>[a-z0-9-]+)'
    r')'
    r'"'
    r'[^>]*>\s*</i>',
    re.IGNORECASE,
)
# Absolute wiki/internal links or image targets: ](/path) or ](/path#frag)
ABS_LINK_RE = re.compile(r"\]\((/(?!/)[^)]*)\)")
CALLOUT_MARKER_RE = re.compile(
    r"\{\.is-(info|warning|danger|success)\}"
)
INLINE_CALLOUT_RE = re.compile(
    r"^(?P<indent>\s*)(?P<body>>?\s*.+?)\s*\{\.is-(?P<kind>info|warning|danger|success)\}\s*$"
)
STANDALONE_MARKER_RE = re.compile(
    r"^(?P<indent>\s*)\{\.is-(?P<kind>info|warning|danger|success)\}\s*$"
)
TABSET_HEADING_RE = re.compile(
    r"^(?P<indent>\s*)(?P<hashes>#{2,6})\s+(?P<title>.*?)\s*\{\.tabset\}\s*$"
)
TABSET_TOC_RE = re.compile(r"^\s*-\s*\[\{\.tabset\}\]\(#tabset\)\s*$")
EMPTY_TAGS_RE = re.compile(r"(?m)^tags:\s*$")


def split_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    raw = text[4:end]
    body = text[end + 5 :]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body


def render_frontmatter(meta: dict[str, str]) -> str:
    kept = {k: v for k, v in meta.items() if k not in FRONTMATTER_DROP}
    if not kept:
        return ""
    lines = ["---"]
    for key in ("title", "description", "tags"):
        if key not in kept:
            continue
        value = kept.pop(key)
        if key == "tags":
            # CSV ("a, b") or already YAML-ish / empty
            if value in ("", "[]", "~", "null"):
                continue
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                items = [i.strip().strip("'\"") for i in inner.split(",") if i.strip()]
            else:
                items = [i.strip().strip("'\"") for i in value.split(",") if i.strip()]
            if not items:
                continue
            lines.append("tags:")
            for item in items:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    for key, value in kept.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def convert_icons(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        if match.group("style"):
            style = ICON_PREFIX.get(match.group("style").lower(), "solid")
            name = match.group("name")
        else:
            style2 = match.group("style2").lower()
            style = {
                "solid": "solid",
                "regular": "regular",
                "brands": "brands",
                "light": "solid",
                "duotone": "solid",
            }.get(style2, "solid")
            name = match.group("name2")
        return f":fontawesome-{style}-{name}:"

    return ICON_RE.sub(repl, text)


def relative_target(source_rel: PurePosixPath, target: str) -> str:
    """Map WikiJS absolute path to a path relative to the source markdown file."""
    from os.path import relpath

    fragment = ""
    path = target
    if "#" in path:
        path, fragment = path.split("#", 1)
        fragment = "#" + fragment
    path = path.rstrip("/")
    if not path:
        return fragment or "."

    asset_exts = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".sh", ".hash"}
    if path in ("/home", "/"):
        dest = "index.md"
    elif path.startswith("/assets/") or path.startswith("/images/") or Path(path).suffix.lower() in asset_exts:
        dest = path.lstrip("/")
    elif path.startswith("/servarr/") and Path(path).suffix:
        dest = path.lstrip("/")
    else:
        dest = path.lstrip("/") + ".md"

    start = source_rel.parent.as_posix()
    if start in ("", "."):
        start = "."
    return f"{relpath(dest, start)}{fragment}"


def convert_absolute_links(text: str, source_rel: PurePosixPath) -> str:
    def repl(match: re.Match[str]) -> str:
        target = match.group(1)
        # Leave anchors-only alone (should not match)
        return f"]({relative_target(source_rel, target)})"

    return ABS_LINK_RE.sub(repl, text)


def indent_block(body: str, indent: str, content_indent: str = "    ") -> str:
    lines = body.splitlines() or [""]
    out = []
    for line in lines:
        if line.strip() == "":
            out.append("")
        else:
            out.append(f"{indent}{content_indent}{line}")
    return "\n".join(out)


def strip_blockquote_prefix(line: str) -> str:
    # Preserve indent, remove single leading ">"
    m = re.match(r"^(\s*)>\s?(.*)$", line)
    if not m:
        return line
    return m.group(2)


def _strip_callout_marker(line: str) -> tuple[str, str | None]:
    match = CALLOUT_MARKER_RE.search(line)
    if not match:
        return line.rstrip(), None
    cleaned = CALLOUT_MARKER_RE.sub("", line).rstrip()
    return cleaned, match.group(1)


def _is_soft_wrap_continuation(line: str, indent: str) -> bool:
    """WikiJS often soft-wraps blockquotes without leading '>' on continuations."""
    if not line.startswith(indent):
        return False
    stripped = line[len(indent) :]
    if stripped == "" or stripped.startswith(">"):
        return False
    if STANDALONE_MARKER_RE.match(line):
        return True
    if stripped.startswith("#"):
        return False
    if stripped.startswith("```") or stripped.startswith("~~~"):
        return False
    if stripped.startswith("- ") or stripped.startswith("* ") or re.match(r"^\d+\.\s", stripped):
        return False
    if stripped.startswith("!!!") or stripped.startswith("==="):
        return False
    return True


def convert_callouts(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        bq = re.match(r"^(\s*)>(?:\s|$).*", line)
        if bq:
            indent = bq.group(1)
            block = [line]
            j = i + 1
            kind = None

            # Explicit additional '>' lines
            while j < len(lines) and re.match(rf"^{re.escape(indent)}>(?:\s|$).*", lines[j]):
                block.append(lines[j])
                j += 1

            # Marker on following line
            if j < len(lines):
                sm = STANDALONE_MARKER_RE.match(lines[j])
                if sm and sm.group("indent") == indent:
                    kind = sm.group("kind")
                    j += 1

            # Soft-wrapped continuations until marker / blank / new block
            if kind is None:
                while j < len(lines) and _is_soft_wrap_continuation(lines[j], indent):
                    cont = lines[j]
                    sm = STANDALONE_MARKER_RE.match(cont)
                    if sm:
                        kind = sm.group("kind")
                        j += 1
                        break
                    cleaned, found = _strip_callout_marker(cont)
                    block.append(cleaned)
                    j += 1
                    if found:
                        kind = found
                        break
                    # Stop at blank (handled by _is_soft_wrap) — if no marker yet, keep going only while continuous

            # Marker trailing any collected blockquote line
            if kind is None:
                rebuilt = []
                for bl in block:
                    cleaned, found = _strip_callout_marker(bl)
                    rebuilt.append(cleaned)
                    if found:
                        kind = found
                block = rebuilt
            else:
                block = [_strip_callout_marker(bl)[0] for bl in block]

            if kind:
                body_lines = [strip_blockquote_prefix(bl) for bl in block]
                while body_lines and body_lines[-1].strip() == "":
                    body_lines.pop()
                body = "\n".join(body_lines).strip("\n")
                out.append(f"{indent}!!! {CALLOUT_TYPES[kind]}")
                out.append(indent_block(body, indent))
                i = j
                continue

            out.extend(block)
            i = j
            continue

        # Non-blockquote line that still carries an inline callout marker
        im = INLINE_CALLOUT_RE.match(line)
        if im and not im.group("body").lstrip().startswith(">"):
            indent = im.group("indent")
            kind = im.group("kind")
            body = im.group("body").strip()
            out.append(f"{indent}!!! {CALLOUT_TYPES[kind]}")
            out.append(indent_block(body, indent))
            i += 1
            continue

        out.append(line)
        i += 1

    cleaned_lines = []
    for line in out:
        if STANDALONE_MARKER_RE.match(line):
            continue
        cleaned_lines.append(CALLOUT_MARKER_RE.sub("", line).rstrip())
    return "\n".join(cleaned_lines) + ("\n" if text.endswith("\n") else "")


def convert_tabsets(text: str) -> str:
    # Drop TOC placeholder entries for tabsets
    lines = [ln for ln in text.splitlines() if not TABSET_TOC_RE.match(ln)]
    out: list[str] = []
    i = 0
    while i < len(lines):
        m = TABSET_HEADING_RE.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue

        indent = m.group("indent")
        hashes = m.group("hashes")
        title = m.group("title").strip()
        tab_level = len(hashes) + 1  # ### under ## {.tabset}
        child_re = re.compile(rf"^{re.escape(indent)}{'#' * tab_level}\s+(?P<tab>.+?)\s*$")
        end_re = re.compile(rf"^{re.escape(indent)}#{{1,{len(hashes)}}}\s+")

        # Optional: keep a plain heading if title present
        if title:
            out.append(f"{indent}{hashes} {title}")
            out.append("")

        i += 1
        # Skip blank lines after heading
        while i < len(lines) and lines[i].strip() == "":
            i += 1

        tabs: list[tuple[str, list[str]]] = []
        current_name: str | None = None
        current_body: list[str] = []

        def flush() -> None:
            nonlocal current_name, current_body
            if current_name is not None:
                tabs.append((current_name, current_body))
            current_name = None
            current_body = []

        while i < len(lines):
            if end_re.match(lines[i]) and not child_re.match(lines[i]):
                break
            cm = child_re.match(lines[i])
            if cm:
                flush()
                current_name = cm.group("tab").strip()
                i += 1
                continue
            if current_name is None:
                # content before first tab — keep outside
                out.append(lines[i])
                i += 1
                continue
            current_body.append(lines[i])
            i += 1
        flush()

        for name, body in tabs:
            # Trim surrounding blank lines
            while body and body[0].strip() == "":
                body.pop(0)
            while body and body[-1].strip() == "":
                body.pop()
            out.append(f'{indent}=== "{name}"')
            out.append("")
            if body:
                out.append(indent_block("\n".join(body), indent))
            else:
                out.append(f"{indent}    ")
            out.append("")
    result = "\n".join(out)
    if text.endswith("\n") and not result.endswith("\n"):
        result += "\n"
    return result


def normalize_whitespace(text: str) -> str:
    """Strip trailing whitespace and ensure a single trailing newline."""
    lines = [line.rstrip() for line in text.splitlines()]
    return "\n".join(lines) + "\n"


def convert_file(content: str, source_rel: PurePosixPath) -> str:
    meta, body = split_frontmatter(content)
    body = convert_icons(body)
    body = convert_callouts(body)
    body = convert_tabsets(body)
    body = convert_absolute_links(body, source_rel)
    # Normalize accidental leftover empty tags key lines in body
    body = EMPTY_TAGS_RE.sub("", body)
    if meta is None:
        return normalize_whitespace(body)
    return normalize_whitespace(render_frontmatter(meta) + body)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="WikiJS markdown file or - for stdin")
    parser.add_argument(
        "--source-rel",
        required=True,
        help="Path of the file relative to docs/ (e.g. lidarr/faq.md or index.md)",
    )
    parser.add_argument("-o", "--output", type=Path, help="Write to file instead of stdout")
    args = parser.parse_args()

    if str(args.input) == "-":
        content = sys.stdin.read()
    else:
        content = args.input.read_text(encoding="utf-8")

    converted = convert_file(content, PurePosixPath(args.source_rel))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(converted, encoding="utf-8")
    else:
        sys.stdout.write(converted)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

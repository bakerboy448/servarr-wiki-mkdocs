#!/usr/bin/env python3
"""Servarr Wiki Migration: WikiJs -> MkDocs Material.

Converts WikiJs markdown content to MkDocs Material format in phases.
Each phase handles a specific conversion concern and commits per directory.
"""

import argparse
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent
AUDIT_LOG = REPO_ROOT / ".migration-audit.log"
MAILMAP = REPO_ROOT / "mailmap.txt"
APP_DIRS = ["sonarr", "radarr", "lidarr", "readarr", "prowlarr", "whisparr", "servarr"]
ROOT_MD_FILES = [
    "bug-report.md",
    "CONTRIBUTING.md",
    "Definitions.md",
    "docker-arm-synology.md",
    "docker-guide.md",
    "donate.md",
    "home.md",
    "install-script.md",
    "lidarr.md",
    "permissions-and-networking.md",
    "prowlarr.md",
    "radarr.md",
    "readarr.md",
    "README.md",
    "sonarr.md",
    "synology-packages.md",
    "useful-tools.md",
    "vpn.md",
    "whisparr.md",
]

ADMONITION_MAP = {
    "is-info": "info",
    "is-warning": "warning",
    "is-danger": "danger",
    "is-success": "success",
    "is-whisparr": "info",
}

ICON_PREFIX_MAP = {
    "fas fa-": "fontawesome-solid-",
    "fab fa-": "fontawesome-brands-",
    "far fa-": "fontawesome-regular-",
    "fa-solid fa-": "fontawesome-solid-",
    "fa-brands fa-": "fontawesome-brands-",
    "fa-regular fa-": "fontawesome-regular-",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def log_audit(message: str) -> None:
    """Append a timestamped message to the migration audit log."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    line = f"[{timestamp}] {message}\n"
    with open(AUDIT_LOG, "a", encoding="utf-8") as fh:
        fh.write(line)


def run_cmd(
    cmd: list[str], *, cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a subprocess command, logging it to the audit log."""
    display = " ".join(cmd)
    log_audit(f"CMD: {display}")
    result = subprocess.run(
        cmd, cwd=cwd or REPO_ROOT, capture_output=True, text=True, check=check
    )
    if result.returncode != 0:
        log_audit(f"CMD FAILED (rc={result.returncode}): {result.stderr.strip()}")
    return result


def git_add_and_commit(
    paths: list[str], message: str, *, add_all: bool = False
) -> None:
    """Stage the given paths and commit with the provided message."""
    if add_all:
        run_cmd(["git", "add", "-A"])
    else:
        for p in paths:
            run_cmd(["git", "add", p])
    # Check if there is anything staged
    result = run_cmd(["git", "diff", "--cached", "--quiet"], check=False)
    if result.returncode == 0:
        log_audit("Nothing staged — skipping commit")
        return
    run_cmd(["git", "commit", "-m", message])
    log_audit(f"COMMIT: {message}")


def get_md_files(directory: Path) -> list[Path]:
    """Return a sorted list of .md files in *directory* (non-recursive)."""
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.md"))


# ---------------------------------------------------------------------------
# Phase 2 — Frontmatter Conversion
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_KEEP_KEYS = {"title", "description", "tags"}
_DROP_KEYS = {"published", "editor", "dateCreated", "date"}


def convert_frontmatter(content: str) -> tuple[str, dict]:
    """Convert WikiJs YAML frontmatter to MkDocs-compatible frontmatter.

    Returns (new_content, changes) where *changes* summarises what was done.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return content, {}

    raw_fm = match.group(1)
    changes: dict = {"kept": [], "dropped": [], "converted": []}
    new_lines: list[str] = []

    for line in raw_fm.splitlines():
        # Simple key: value parsing (good enough for flat WikiJs frontmatter)
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()

        if key in _DROP_KEYS:
            changes["dropped"].append(key)
            continue

        if key == "tags":
            # Comma-separated string → YAML list
            tags = [t.strip() for t in value.split(",") if t.strip()]
            if tags:
                new_lines.append("tags:")
                for tag in tags:
                    new_lines.append(f"  - {tag}")
                changes["converted"].append("tags")
            continue

        if key in _KEEP_KEYS:
            new_lines.append(f"{key}: {value}")
            changes["kept"].append(key)

    if not new_lines:
        # Remove empty frontmatter entirely
        new_content = content[match.end() :]
    else:
        new_fm = "\n".join(new_lines)
        new_content = f"---\n{new_fm}\n---\n{content[match.end() :]}"

    return new_content, changes


def _convert_dir_frontmatter(directory: Path, scope: str, dry_run: bool) -> None:
    """Process frontmatter for every .md file in *directory*, then commit."""
    md_files = get_md_files(directory)
    if not md_files:
        return

    changed_paths: list[str] = []
    for md_file in md_files:
        original = md_file.read_text(encoding="utf-8")
        converted, changes = convert_frontmatter(original)
        if converted != original:
            if dry_run:
                log_audit(
                    f"DRY-RUN would convert frontmatter: {md_file.relative_to(REPO_ROOT)}"
                )
                print(f"  [dry-run] {md_file.relative_to(REPO_ROOT)}: {changes}")
            else:
                md_file.write_text(converted, encoding="utf-8")
                changed_paths.append(str(md_file.relative_to(REPO_ROOT)))
                log_audit(
                    f"Converted frontmatter: {md_file.relative_to(REPO_ROOT)} — {changes}"
                )

    if changed_paths and not dry_run:
        git_add_and_commit(
            changed_paths,
            f"refactor({scope}): convert WikiJs frontmatter to MkDocs format",
        )


def phase_2_frontmatter(dry_run: bool) -> None:
    """Phase 2: Convert WikiJs frontmatter across every directory."""
    log_audit("=== Phase 2: Frontmatter Conversion ===")

    # Root .md files
    _convert_dir_frontmatter(REPO_ROOT, "root", dry_run)

    # App directories
    for app in APP_DIRS:
        app_dir = REPO_ROOT / app
        if app_dir.is_dir():
            _convert_dir_frontmatter(app_dir, app, dry_run)
            # Recurse one level into sub-directories
            for sub in sorted(app_dir.iterdir()):
                if sub.is_dir():
                    _convert_dir_frontmatter(sub, f"{app}/{sub.name}", dry_run)

    log_audit("=== Phase 2 complete ===")


# ---------------------------------------------------------------------------
# Phase 3 — Admonition Conversion
# ---------------------------------------------------------------------------

_ADMONITION_CLASSES = "|".join(re.escape(k) for k in ADMONITION_MAP)

# Pattern 1: multi-line blockquote followed by {.is-xxx} on next line
_ADMONITION_BLOCK_RE = re.compile(
    r"((?:^>.*\n?)+)\{\.(" + _ADMONITION_CLASSES + r")\}",
    re.MULTILINE,
)

# Pattern 2: inline class on the same line as the blockquote text
_ADMONITION_INLINE_RE = re.compile(
    r"^(>.+?)\{\.(" + _ADMONITION_CLASSES + r")\}\s*$",
    re.MULTILINE,
)


def _blockquote_to_admonition(block_text: str, adm_type: str) -> str:
    """Convert a blockquote block into an MkDocs admonition."""
    lines = block_text.splitlines()
    body_lines: list[str] = []
    for line in lines:
        # Strip leading '>' and optional single space
        stripped = re.sub(r"^>\s?", "", line)
        body_lines.append(stripped)

    # Remove leading/trailing empty lines from body
    while body_lines and not body_lines[0].strip():
        body_lines.pop(0)
    while body_lines and not body_lines[-1].strip():
        body_lines.pop()

    result_lines = [f"!!! {adm_type}"]
    for bline in body_lines:
        if bline.strip() == "":
            result_lines.append("")
        else:
            result_lines.append(f"    {bline}")

    return "\n".join(result_lines)


def convert_admonitions(content: str) -> tuple[str, int]:
    """Convert WikiJs blockquote admonitions to MkDocs admonition syntax.

    Returns (new_content, count_of_conversions).
    """
    count = 0

    def _replace_block(m: re.Match) -> str:
        nonlocal count
        count += 1
        block_text = m.group(1)
        adm_class = m.group(2)
        adm_type = ADMONITION_MAP[adm_class]
        return _blockquote_to_admonition(block_text, adm_type)

    content = _ADMONITION_BLOCK_RE.sub(_replace_block, content)

    def _replace_inline(m: re.Match) -> str:
        nonlocal count
        count += 1
        raw_line = m.group(1)
        adm_class = m.group(2)
        adm_type = ADMONITION_MAP[adm_class]
        text = re.sub(r"^>\s?", "", raw_line).strip()
        return f"!!! {adm_type}\n    {text}"

    content = _ADMONITION_INLINE_RE.sub(_replace_inline, content)

    # Pass 3: indented blockquotes (  > text or    > text) followed by {.is-xxx}
    _indented_block_re = re.compile(
        r"((?:^[ \t]+>.*\n?)+)\s*\{\.(" + _ADMONITION_CLASSES + r")\}",
        re.MULTILINE,
    )

    def _replace_indented_block(m: re.Match) -> str:
        nonlocal count
        count += 1
        block_text = m.group(1)
        adm_class = m.group(2)
        adm_type = ADMONITION_MAP[adm_class]
        lines = block_text.splitlines()
        body_lines: list[str] = []
        for line in lines:
            stripped = re.sub(r"^[ \t]*>[ \t]?", "", line)
            body_lines.append(stripped)
        while body_lines and not body_lines[0].strip():
            body_lines.pop(0)
        while body_lines and not body_lines[-1].strip():
            body_lines.pop()
        result = [f"!!! {adm_type}"]
        for bline in body_lines:
            if bline.strip() == "":
                result.append("")
            else:
                result.append(f"    {bline}")
        return "\n".join(result)

    content = _indented_block_re.sub(_replace_indented_block, content)

    # Pass 4: indented blockquote with inline class (  > text{.is-xxx})
    _indented_inline_re = re.compile(
        r"^([ \t]+>.+?)\{\.(" + _ADMONITION_CLASSES + r")\}\s*$",
        re.MULTILINE,
    )

    def _replace_indented_inline(m: re.Match) -> str:
        nonlocal count
        count += 1
        raw_line = m.group(1)
        adm_class = m.group(2)
        adm_type = ADMONITION_MAP[adm_class]
        text = re.sub(r"^[ \t]*>[ \t]?", "", raw_line).strip()
        return f"!!! {adm_type}\n    {text}"

    content = _indented_inline_re.sub(_replace_indented_inline, content)

    # Pass 5: list-blockquote combos (- > text{.is-xxx} or   - > text{.is-xxx})
    _list_bq_re = re.compile(
        r"^([ \t]*-\s+>.+?)\{\.(" + _ADMONITION_CLASSES + r")\}\s*$",
        re.MULTILINE,
    )

    def _replace_list_bq(m: re.Match) -> str:
        nonlocal count
        count += 1
        raw_line = m.group(1)
        adm_class = m.group(2)
        adm_type = ADMONITION_MAP[adm_class]
        text = re.sub(r"^[ \t]*-\s+>[ \t]?", "", raw_line).strip()
        return f"!!! {adm_type}\n    {text}"

    content = _list_bq_re.sub(_replace_list_bq, content)

    # Pass 6: non-blockquote text with inline class (text{.is-xxx} or text {.is-xxx})
    _plain_inline_re = re.compile(
        r"^(.+?)\s*\{\.(" + _ADMONITION_CLASSES + r")\}\s*$",
        re.MULTILINE,
    )

    def _replace_plain_inline(m: re.Match) -> str:
        nonlocal count
        text = m.group(1).strip()
        adm_class = m.group(2)
        adm_type = ADMONITION_MAP[adm_class]
        # Skip if this is already an admonition or looks like a heading
        if text.startswith("!!!") or text.startswith("#"):
            return m.group(0)
        count += 1
        return f"!!! {adm_type}\n    {text}"

    content = _plain_inline_re.sub(_replace_plain_inline, content)

    # Pass 7: standalone {.is-xxx} on its own line (class preceded by blockquote block above)
    # These are orphaned markers where the blockquote was already converted or
    # the blockquote ended on the previous line
    _standalone_re = re.compile(
        r"^[ \t]*\{\.(" + _ADMONITION_CLASSES + r")\}\s*$",
        re.MULTILINE,
    )

    # For standalone markers, we need to find the preceding blockquote and convert it
    def _handle_standalone_markers(text: str) -> str:
        nonlocal count
        lines = text.split("\n")
        result: list[str] = []
        i = 0
        while i < len(lines):
            m = _standalone_re.match(lines[i])
            if m:
                adm_class = m.group(1)
                adm_type = ADMONITION_MAP[adm_class]
                # Look backwards to find preceding blockquote lines
                bq_lines: list[str] = []
                while result and re.match(r"^[ \t]*>", result[-1]):
                    bq_lines.insert(0, result.pop())
                if bq_lines:
                    count += 1
                    body = []
                    for bql in bq_lines:
                        stripped = re.sub(r"^[ \t]*>[ \t]?", "", bql)
                        body.append(stripped)
                    while body and not body[0].strip():
                        body.pop(0)
                    while body and not body[-1].strip():
                        body.pop()
                    result.append(f"!!! {adm_type}")
                    for bl in body:
                        if bl.strip() == "":
                            result.append("")
                        else:
                            result.append(f"    {bl}")
                else:
                    # No preceding blockquote — just remove the orphan marker
                    pass
            else:
                result.append(lines[i])
            i += 1
        return "\n".join(result)

    content = _handle_standalone_markers(content)

    return content, count


def _convert_dir_admonitions(directory: Path, scope: str, dry_run: bool) -> None:
    """Process admonitions for every .md file in *directory*, then commit."""
    md_files = get_md_files(directory)
    if not md_files:
        return

    changed_paths: list[str] = []
    total_count = 0
    for md_file in md_files:
        original = md_file.read_text(encoding="utf-8")
        converted, count = convert_admonitions(original)
        if converted != original:
            total_count += count
            if dry_run:
                log_audit(
                    f"DRY-RUN would convert {count} admonitions: {md_file.relative_to(REPO_ROOT)}"
                )
                print(
                    f"  [dry-run] {md_file.relative_to(REPO_ROOT)}: {count} admonitions"
                )
            else:
                md_file.write_text(converted, encoding="utf-8")
                changed_paths.append(str(md_file.relative_to(REPO_ROOT)))
                log_audit(
                    f"Converted {count} admonitions: {md_file.relative_to(REPO_ROOT)}"
                )

    if changed_paths and not dry_run:
        git_add_and_commit(
            changed_paths,
            f"refactor({scope}): convert WikiJs admonitions to MkDocs format ({total_count} blocks)",
        )


def phase_3_admonitions(dry_run: bool) -> None:
    """Phase 3: Convert WikiJs admonitions to MkDocs admonition syntax."""
    log_audit("=== Phase 3: Admonition Conversion ===")

    _convert_dir_admonitions(REPO_ROOT, "root", dry_run)

    for app in APP_DIRS:
        app_dir = REPO_ROOT / app
        if app_dir.is_dir():
            _convert_dir_admonitions(app_dir, app, dry_run)
            for sub in sorted(app_dir.iterdir()):
                if sub.is_dir():
                    _convert_dir_admonitions(sub, f"{app}/{sub.name}", dry_run)

    log_audit("=== Phase 3 complete ===")


# ---------------------------------------------------------------------------
# Phase 4 — Layout Patterns
# ---------------------------------------------------------------------------


def convert_links_list(content: str) -> tuple[str, int]:
    """Remove {.links-list} markers from content.

    Returns (new_content, count_of_removals).
    """
    new_content, count = re.subn(r"\s*\{\.links-list\}", "", content)
    return new_content, count


def convert_tabsets(content: str) -> tuple[str, int]:
    """Convert WikiJs {.tabset} syntax to pymdownx.tabbed === syntax.

    Returns (new_content, count_of_tabsets_converted).
    """
    lines = content.splitlines(keepends=True)
    result: list[str] = []
    count = 0
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip("\n\r")

        # Detect a heading with {.tabset}
        tabset_match = re.match(r"^(#{1,6})\s+.*\{\.tabset\}\s*$", stripped)
        if not tabset_match:
            result.append(line)
            i += 1
            continue

        # Found a tabset heading
        count += 1
        parent_level = len(tabset_match.group(1))
        child_level = parent_level + 1
        i += 1  # skip the tabset heading line itself

        # Now process child tabs until we hit a heading at parent_level or higher
        in_tab = False
        while i < len(lines):
            line = lines[i]
            stripped = line.rstrip("\n\r")

            # Check if this line is a heading
            heading_match = re.match(r"^(#{1,6})\s+(.*?)\s*$", stripped)
            if heading_match:
                hl = len(heading_match.group(1))
                if hl <= parent_level:
                    # End of tabset — don't consume this line
                    break
                if hl == child_level:
                    # New tab
                    tab_title = heading_match.group(2).strip()
                    result.append(f'=== "{tab_title}"\n')
                    result.append("\n")
                    in_tab = True
                    i += 1
                    continue
                # Deeper heading — part of tab content
                if in_tab:
                    result.append(f"    {line}")
                else:
                    result.append(line)
                i += 1
                continue

            # Regular content line
            if in_tab:
                if stripped == "":
                    result.append("\n")
                else:
                    result.append(f"    {line}")
            else:
                result.append(line)
            i += 1

    return "".join(result), count


def convert_grid_list(content: str) -> tuple[str, int]:
    """Remove {.grid-list} markers from content.

    Returns (new_content, count_of_removals).
    """
    new_content, count = re.subn(r"\s*\{\.grid-list\}", "", content)
    return new_content, count


def _process_layout_pattern(
    pattern_name: str,
    converter,
    commit_suffix: str,
    dry_run: bool,
) -> None:
    """Apply a layout converter across all directories and commit once per pattern."""
    changed_paths: list[str] = []
    total_count = 0

    def _scan_dir(directory: Path) -> None:
        nonlocal total_count
        for md_file in get_md_files(directory):
            original = md_file.read_text(encoding="utf-8")
            converted, count = converter(original)
            if converted != original:
                total_count += count
                rel = md_file.relative_to(REPO_ROOT)
                if dry_run:
                    log_audit(f"DRY-RUN would convert {count} {pattern_name}: {rel}")
                    print(f"  [dry-run] {rel}: {count} {pattern_name}")
                else:
                    md_file.write_text(converted, encoding="utf-8")
                    changed_paths.append(str(rel))
                    log_audit(f"Converted {count} {pattern_name}: {rel}")

    _scan_dir(REPO_ROOT)
    for app in APP_DIRS:
        app_dir = REPO_ROOT / app
        if app_dir.is_dir():
            _scan_dir(app_dir)
            for sub in sorted(app_dir.iterdir()):
                if sub.is_dir():
                    _scan_dir(sub)

    if changed_paths and not dry_run:
        git_add_and_commit(
            changed_paths,
            f"refactor: {commit_suffix} ({total_count} instances)",
        )


def phase_4_layout(dry_run: bool) -> None:
    """Phase 4: Convert layout patterns (links-list, tabsets, grid-list)."""
    log_audit("=== Phase 4: Layout Patterns ===")

    _process_layout_pattern(
        "links-list",
        convert_links_list,
        "remove WikiJs links-list markers",
        dry_run,
    )
    _process_layout_pattern(
        "tabset",
        convert_tabsets,
        "convert WikiJs tabsets to pymdownx.tabbed syntax",
        dry_run,
    )
    _process_layout_pattern(
        "grid-list",
        convert_grid_list,
        "remove WikiJs grid-list markers",
        dry_run,
    )

    log_audit("=== Phase 4 complete ===")


# ---------------------------------------------------------------------------
# Phase 5 — Icon Conversion
# ---------------------------------------------------------------------------

_ICON_RE = re.compile(r'<i\s+class="([^"]+)"[^>]*>\s*</i>')


def convert_icons(content: str) -> tuple[str, int]:
    """Convert HTML <i class="..."> icons to MkDocs :icon: syntax.

    Returns (new_content, count_of_conversions).
    """
    count = 0

    def _replace_icon(m: re.Match) -> str:
        nonlocal count
        class_attr = m.group(1).strip()

        for prefix, replacement in ICON_PREFIX_MAP.items():
            if class_attr.startswith(prefix):
                icon_name = class_attr[len(prefix) :]
                count += 1
                return f":{replacement}{icon_name}:"

        # Unknown prefix — leave as-is
        log_audit(f"Unknown icon class: {class_attr}")
        return m.group(0)

    new_content = _ICON_RE.sub(_replace_icon, content)
    return new_content, count


def _convert_dir_icons(directory: Path, scope: str, dry_run: bool) -> None:
    """Process icons for every .md file in *directory*, then commit."""
    md_files = get_md_files(directory)
    if not md_files:
        return

    changed_paths: list[str] = []
    total_count = 0
    for md_file in md_files:
        original = md_file.read_text(encoding="utf-8")
        converted, count = convert_icons(original)
        if converted != original:
            total_count += count
            rel = md_file.relative_to(REPO_ROOT)
            if dry_run:
                log_audit(f"DRY-RUN would convert {count} icons: {rel}")
                print(f"  [dry-run] {rel}: {count} icons")
            else:
                md_file.write_text(converted, encoding="utf-8")
                changed_paths.append(str(rel))
                log_audit(f"Converted {count} icons: {rel}")

    if changed_paths and not dry_run:
        git_add_and_commit(
            changed_paths,
            f"refactor({scope}): convert WikiJs icons to MkDocs format ({total_count} icons)",
        )


def phase_5_icons(dry_run: bool) -> None:
    """Phase 5: Convert FontAwesome HTML icons to MkDocs icon syntax."""
    log_audit("=== Phase 5: Icon Conversion ===")

    _convert_dir_icons(REPO_ROOT, "root", dry_run)

    for app in APP_DIRS:
        app_dir = REPO_ROOT / app
        if app_dir.is_dir():
            _convert_dir_icons(app_dir, app, dry_run)
            for sub in sorted(app_dir.iterdir()):
                if sub.is_dir():
                    _convert_dir_icons(sub, f"{app}/{sub.name}", dry_run)

    log_audit("=== Phase 5 complete ===")


# ---------------------------------------------------------------------------
# Phase 6 — Structure (move into docs/)
# ---------------------------------------------------------------------------


def phase_6_structure(dry_run: bool) -> None:
    """Phase 6: Restructure repository for MkDocs docs/ layout."""
    log_audit("=== Phase 6: Structure ===")

    docs_dir = REPO_ROOT / "docs"

    if dry_run:
        print("  [dry-run] Would create docs/ and move files into it")
        log_audit("DRY-RUN would restructure into docs/")
        log_audit("=== Phase 6 complete (dry-run) ===")
        return

    docs_dir.mkdir(exist_ok=True)

    # Move root .md files
    for md_name in ROOT_MD_FILES:
        src = REPO_ROOT / md_name
        if not src.exists():
            continue
        if md_name == "home.md":
            dst = docs_dir / "index.md"
        else:
            dst = docs_dir / md_name
        shutil.move(str(src), str(dst))
        log_audit(f"Moved {md_name} -> docs/{dst.name}")

    # Move APP_DIRS
    for app in APP_DIRS:
        src = REPO_ROOT / app
        if src.is_dir():
            dst = docs_dir / app
            shutil.move(str(src), str(dst))
            log_audit(f"Moved {app}/ -> docs/{app}/")

    # Move assets/
    assets_src = REPO_ROOT / "assets"
    if assets_src.is_dir():
        assets_dst = docs_dir / "assets"
        shutil.move(str(assets_src), str(assets_dst))
        log_audit("Moved assets/ -> docs/assets/")

    git_add_and_commit(
        [], "refactor: restructure repository for MkDocs docs/ layout", add_all=True
    )

    # Create .pages files for navigation ordering
    _create_pages_files(docs_dir)
    git_add_and_commit(
        [], "refactor: add .pages files for navigation ordering", add_all=True
    )

    # Create CONTRIBUTING.md with MkDocs dev instructions
    _create_contributing(REPO_ROOT)
    git_add_and_commit(
        [str((REPO_ROOT / "CONTRIBUTING.md").relative_to(REPO_ROOT))],
        "docs: add CONTRIBUTING.md with MkDocs development instructions",
    )

    log_audit("=== Phase 6 complete ===")


def _create_pages_files(docs_dir: Path) -> None:
    """Create awesome-pages .pages files for navigation ordering."""
    # Root docs .pages
    root_pages = [
        "nav:",
        "  - index.md",
        "  - sonarr",
        "  - radarr",
        "  - lidarr",
        "  - readarr",
        "  - prowlarr",
        "  - whisparr",
        "  - servarr",
        "  - Definitions.md",
        "  - useful-tools.md",
        "  - permissions-and-networking.md",
        "  - docker-guide.md",
        "  - docker-arm-synology.md",
        "  - synology-packages.md",
        "  - install-script.md",
        "  - vpn.md",
        "  - donate.md",
        "  - bug-report.md",
        "  - CONTRIBUTING.md",
    ]
    (docs_dir / ".pages").write_text("\n".join(root_pages) + "\n", encoding="utf-8")
    log_audit("Created docs/.pages")

    # Per-app .pages (simple title)
    for app in APP_DIRS:
        app_dir = docs_dir / app
        if app_dir.is_dir():
            title = app.capitalize()
            (app_dir / ".pages").write_text(f"title: {title}\n", encoding="utf-8")
            log_audit(f"Created docs/{app}/.pages")


def _create_contributing(repo_root: Path) -> None:
    """Create a CONTRIBUTING.md with MkDocs development instructions at repo root."""
    content = """\
# Contributing to the Servarr Wiki

## Development Setup

1. Install Python 3.10+ and pip
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Start the local development server:

   ```bash
   mkdocs serve
   ```

4. Open <http://localhost:8000> in your browser.

## Writing Documentation

- All documentation lives in the `docs/` directory.
- Use [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) syntax.
- Admonitions use `!!! type` syntax (not blockquotes).
- Tabs use `=== "Tab Title"` syntax.
- Icons use `:fontawesome-solid-icon-name:` syntax.

## Building

```bash
mkdocs build --strict
```

This validates all links and ensures the site builds cleanly.
"""
    (repo_root / "CONTRIBUTING.md").write_text(content, encoding="utf-8")
    log_audit("Created CONTRIBUTING.md at repo root")


# ---------------------------------------------------------------------------
# Phase 7 — Cross-page Links
# ---------------------------------------------------------------------------

# Matches [text](/path) or [text](/path#anchor) — only absolute internal paths
_INTERNAL_LINK_RE = re.compile(r"(\[[^\]]*\]\()(/[^)#\s]+)(#[^)\s]*)?\s*(\))")


def convert_internal_links(content: str, file_path: Path) -> tuple[str, int]:
    """Convert WikiJs absolute internal links to MkDocs relative links.

    Expects *file_path* to be the file's path relative to docs/ root.
    Returns (new_content, count_of_conversions).
    """
    # Determine relative depth from file's directory to docs root
    file_dir = file_path.parent
    # Number of levels up from file to docs root
    depth = len(file_dir.parts)

    count = 0

    def _replace_link(m: re.Match) -> str:
        nonlocal count
        prefix = m.group(1)  # [text](
        path = m.group(2)  # /sonarr/settings
        anchor = m.group(3) or ""  # #anchor or empty
        suffix = m.group(4)  # )

        # Skip protocol links (shouldn't match but be safe)
        if path.startswith("//") or "://" in path:
            return m.group(0)

        count += 1

        # Remove leading slash
        rel_path = path.lstrip("/")

        # Add .md extension if no file extension present
        path_obj = Path(rel_path)
        if not path_obj.suffix:
            rel_path = rel_path + ".md"

        # Build relative path from current file to target
        if depth == 0:
            final_path = rel_path
        else:
            up = "/".join([".."] * depth)
            final_path = f"{up}/{rel_path}"

        return f"{prefix}{final_path}{anchor}{suffix}"

    new_content = _INTERNAL_LINK_RE.sub(_replace_link, content)
    return new_content, count


def _convert_dir_links(
    directory: Path, docs_root: Path, scope: str, dry_run: bool
) -> None:
    """Process internal links for every .md file in *directory*, then commit."""
    md_files = get_md_files(directory)
    if not md_files:
        return

    changed_paths: list[str] = []
    total_count = 0
    for md_file in md_files:
        original = md_file.read_text(encoding="utf-8")
        rel_to_docs = md_file.relative_to(docs_root)
        converted, count = convert_internal_links(original, rel_to_docs)
        if converted != original:
            total_count += count
            rel = md_file.relative_to(REPO_ROOT)
            if dry_run:
                log_audit(f"DRY-RUN would convert {count} links: {rel}")
                print(f"  [dry-run] {rel}: {count} internal links")
            else:
                md_file.write_text(converted, encoding="utf-8")
                changed_paths.append(str(rel))
                log_audit(f"Converted {count} internal links: {rel}")

    if changed_paths and not dry_run:
        git_add_and_commit(
            changed_paths,
            f"refactor({scope}): convert WikiJs internal links to MkDocs relative links ({total_count} links)",
        )


def phase_7_links(dry_run: bool) -> None:
    """Phase 7: Convert WikiJs absolute internal links to MkDocs relative links."""
    log_audit("=== Phase 7: Cross-page Links ===")

    docs_dir = REPO_ROOT / "docs"
    if not docs_dir.is_dir():
        log_audit("ERROR: docs/ directory not found — run phase 6 first")
        print("Error: docs/ directory not found. Run phase 6 first.")
        return

    # Root docs files
    _convert_dir_links(docs_dir, docs_dir, "root", dry_run)

    # App directories
    for app in APP_DIRS:
        app_dir = docs_dir / app
        if app_dir.is_dir():
            _convert_dir_links(app_dir, docs_dir, app, dry_run)
            for sub in sorted(app_dir.iterdir()):
                if sub.is_dir():
                    _convert_dir_links(sub, docs_dir, f"{app}/{sub.name}", dry_run)

    log_audit("=== Phase 7 complete ===")


# ---------------------------------------------------------------------------
# Phase 8 — SEO
# ---------------------------------------------------------------------------


def phase_8_seo(dry_run: bool) -> None:
    """Phase 8: Create robots.txt and llms.txt in docs/."""
    log_audit("=== Phase 8: SEO ===")

    docs_dir = REPO_ROOT / "docs"
    if not docs_dir.is_dir():
        log_audit("ERROR: docs/ directory not found — run phase 6 first")
        print("Error: docs/ directory not found. Run phase 6 first.")
        return

    robots_content = """\
User-agent: *
Allow: /

Sitemap: https://wiki.servarr.com/sitemap.xml
"""

    llms_content = """\
# Servarr Wiki

> Documentation for Sonarr, Radarr, Lidarr, Readarr, Prowlarr, and Whisparr.

This is the official wiki for the Servarr family of applications — PVR (Personal Video Recorder)
and related media automation tools.

## Main Sections

- [Sonarr](/sonarr/) — TV Series management
- [Radarr](/radarr/) — Movie management
- [Lidarr](/lidarr/) — Music management
- [Readarr](/readarr/) — Book management
- [Prowlarr](/prowlarr/) — Indexer management
- [Whisparr](/whisparr/) — Adult content management

## Common Topics

- [Docker Guide](/docker-guide/)
- [Permissions and Networking](/permissions-and-networking/)
- [Useful Tools](/useful-tools/)
- [Definitions](/Definitions/)
"""

    if dry_run:
        print("  [dry-run] Would create docs/robots.txt")
        print("  [dry-run] Would create docs/llms.txt")
        log_audit("DRY-RUN would create robots.txt and llms.txt")
    else:
        (docs_dir / "robots.txt").write_text(robots_content, encoding="utf-8")
        log_audit("Created docs/robots.txt")
        (docs_dir / "llms.txt").write_text(llms_content, encoding="utf-8")
        log_audit("Created docs/llms.txt")
        git_add_and_commit(
            ["docs/robots.txt", "docs/llms.txt"],
            "feat: add robots.txt and llms.txt for SEO",
        )

    log_audit("=== Phase 8 complete ===")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Servarr Wiki Migration: WikiJs \u2192 MkDocs Material",
    )
    parser.add_argument("--phase", type=int, help="Run specific phase (2-8)")
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )
    args = parser.parse_args()

    phases = {
        2: phase_2_frontmatter,
        3: phase_3_admonitions,
        4: phase_4_layout,
        5: phase_5_icons,
        6: phase_6_structure,
        7: phase_7_links,
        8: phase_8_seo,
    }

    if args.phase:
        if args.phase not in phases:
            print(f"Unknown phase: {args.phase}")
            sys.exit(1)
        phases[args.phase](args.dry_run)
    else:
        for phase_num in sorted(phases):
            phases[phase_num](args.dry_run)


if __name__ == "__main__":
    main()

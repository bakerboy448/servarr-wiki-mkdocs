#!/usr/bin/env bash
# Sync Servarr/Wiki upstream content into docs/ and convert WikiJS -> MkDocs.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
UPSTREAM_REF="${1:-upstream/master}"
TMP="$(mktemp -d)"
PRESERVE_TMP="$(mktemp -d)"
trap 'rm -rf "$TMP" "$PRESERVE_TMP"' EXIT

cd "$ROOT"

echo "==> Exporting ${UPSTREAM_REF}"
git archive "$UPSTREAM_REF" | tar -x -C "$TMP"

echo "==> Preserving mkdocs-only paths"
PRESERVE_LIST=(
  "stylesheets"
  "llms.txt"
  "robots.txt"
  ".pages"
  "sonarr/.pages"
  "radarr/.pages"
  "lidarr/.pages"
  "readarr/.pages"
  "prowlarr/.pages"
  "whisparr/.pages"
  "servarr/.pages"
)
for path in "${PRESERVE_LIST[@]}"; do
  if [[ -e "$ROOT/docs/$path" ]]; then
    mkdir -p "$PRESERVE_TMP/$(dirname "$path")"
    cp -a "$ROOT/docs/$path" "$PRESERVE_TMP/$path"
  fi
done

echo "==> Replacing docs content from upstream"
# Remove regenerable content; keep nothing else under docs except we'll restore preserve list
find "$ROOT/docs" -mindepth 1 -maxdepth 1 -exec rm -rf {} +

mkdir -p "$ROOT/docs/assets" "$ROOT/docs/images" "$ROOT/docs/servarr"

if [[ -d "$TMP/assets" ]]; then
  cp -a "$TMP/assets/." "$ROOT/docs/assets/"
fi
if [[ -d "$TMP/images" ]]; then
  cp -a "$TMP/images/." "$ROOT/docs/images/"
  mkdir -p "$ROOT/images"
  cp -a "$TMP/images/." "$ROOT/images/"
fi
if [[ -d "$TMP/servarr" ]]; then
  # scripts + any wiki pages under servarr/
  cp -a "$TMP/servarr/." "$ROOT/docs/servarr/"
fi
if [[ -f "$TMP/dbrecover.gif" ]]; then
  cp -a "$TMP/dbrecover.gif" "$ROOT/dbrecover.gif"
  cp -a "$TMP/dbrecover.gif" "$ROOT/docs/dbrecover.gif"
fi
if [[ -f "$TMP/.typos.toml" ]]; then
  cp -a "$TMP/.typos.toml" "$ROOT/.typos.toml"
fi

# App-scoped binary assets (e.g. lidarr/images/*.png) live beside markdown upstream
for app in lidarr radarr readarr sonarr whisparr prowlarr; do
  if [[ -d "$TMP/$app" ]]; then
    while IFS= read -r -d '' f; do
      rel="${f#"$TMP/"}"
      mkdir -p "$ROOT/docs/$(dirname "$rel")"
      cp -a "$f" "$ROOT/docs/$rel"
    done < <(find "$TMP/$app" -type f ! -name '*.md' -print0)
  fi
done

PYTHON="$ROOT/scripts/wikijs_to_mkdocs.py"
converted=0
skipped=0

while IFS= read -r -d '' src; do
  rel="${src#"$TMP/"}"
  case "$rel" in
    home.md) dest_rel="index.md" ;;
    README.md | CONTRIBUTING.md)
      skipped=$((skipped + 1))
      continue
      ;;
    *) dest_rel="$rel" ;;
  esac
  # servarr/*.sh already copied; only convert markdown under servarr/
  dest="$ROOT/docs/$dest_rel"
  mkdir -p "$(dirname "$dest")"
  python3 "$PYTHON" "$src" --source-rel "$dest_rel" -o "$dest"
  converted=$((converted + 1))
done < <(find "$TMP" -type f -name '*.md' -print0)

echo "==> Restoring mkdocs-only paths"
for path in "${PRESERVE_LIST[@]}"; do
  if [[ -e "$PRESERVE_TMP/$path" ]]; then
    mkdir -p "$ROOT/docs/$(dirname "$path")"
    rm -rf "$ROOT/docs/$path"
    cp -a "$PRESERVE_TMP/$path" "$ROOT/docs/$path"
  fi
done

echo "==> Converted ${converted} markdown files (skipped ${skipped})"
echo "==> Checking for WikiJS leakage"
set +e
leaks="$(rg -n --glob '*.md' \
  '\{\.is-(info|warning|danger|success)\}|<i class="fa|^(published|dateCreated|editor):' \
  "$ROOT/docs" 2>/dev/null)"
set -e
if [[ -n "${leaks}" ]]; then
  echo "$leaks" >&2
  echo "ERROR: WikiJS markers remain after conversion" >&2
  exit 1
fi
echo "==> Sync complete from ${UPSTREAM_REF} ($(git rev-parse --short "$UPSTREAM_REF"))"

> Global rules: ~/.claude/CLAUDE.md

## Overview

MkDocs-based mirror of the Servarr wiki (lidarr, radarr, readarr, sonarr, whisparr, prowlarr). Material theme with plugins for search, glightbox gallery, minification, git-revision dates, and awesome-pages nav management.

## Key Files / Layout

- `mkdocs.yml` — site config, theme (material), plugins, nav structure
- `docs/` — source markdown organized by app (lidarr/, radarr/, readarr/, sonarr/, whisparr/, prowlarr/); generic docs (docker-guide.md, install-script.md, permissions-and-networking.md)
- `.pages` — awesome-pages nav ordering
- `requirements.txt` — mkdocs-material 9.7.6 + plugins, prowlarr indexer update script (requests, pycountry, python-iso639)
- `.github/workflows/` — pr-preview.yml (GH Pages preview on PRs), pre-commit.yml, prowlarr-ci.yml

## Build / Run / Deploy

- **Install:** `pip install -r requirements.txt`
- **Serve locally:** `mkdocs serve` (hot-reload on `http://localhost:8000`)
- **Build static:** `mkdocs build` (output to `site/`)
- **Deploy:** PR previews auto-deploy to GitHub Pages via `actions-gh-pages` (publish_dir: ./site, destination_dir: pr-preview/pr-$NUMBER)

## Gotchas

- **Strict mode disabled** (`strict: false` in mkdocs.yml) — 384 broken anchor warnings (#problem-not-listed-1, #windows-multi, etc. in whisparr, readarr, sonarr docs). Re-enable after fixing.
- **Material social plugin** enabled but requires `mkdocs-social-plugin` (or similar) to render social cards; verify installed if building for card generation.

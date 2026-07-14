# servarr-wiki-mkdocs

MkDocs Material build of the [Servarr Wiki](https://github.com/Servarr/Wiki) (Lidarr, Radarr, Readarr, Sonarr, Whisparr, Prowlarr).

Upstream WikiJS markdown is converted to MkDocs Material (admonitions, icons, relative links, tabsets) and published from this repository.

> **Upstream sync:** Servarr/Wiki `578505a7` (2026-07-13)

## Quick start

```bash
pip install -r requirements.txt
mkdocs serve
```

Open <http://localhost:8000>.

```bash
mkdocs build
```

Static output is written to `site/`.

## Syncing from Servarr/Wiki

```bash
git remote add upstream https://github.com/Servarr/Wiki.git   # once
git fetch upstream master
bash scripts/sync_upstream_wiki.sh upstream/master
```

This refreshes `docs/` from upstream and runs `scripts/wikijs_to_mkdocs.py`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Prefer fixing content upstream in [Servarr/Wiki](https://github.com/Servarr/Wiki) when possible; this repo focuses on the MkDocs presentation layer and sync tooling.

Issue and PR templates live under [`.github/`](.github/). Use **Content bug** vs **Site / tooling bug** so maintainers can route work correctly.

## Deployment

| Target | Status | Notes |
|--------|--------|-------|
| GitHub Pages | Primary, active | `.github/workflows/gh-pages.yml` deploys `main` on every push; `pr-preview.yml` deploys PR previews to `pr-preview/pr-N/` |
| Cloudflare Pages | Optional, gated | `wrangler.toml` + `.github/workflows/cloudflare-pages.yml`; off by default |

GitHub Pages needs no secrets beyond the default `GITHUB_TOKEN` — this is what makes the repo trivially self-hostable on a fork. Cloudflare is opt-in, gated behind repository secrets/`CF_PAGES_DEPLOY`. Setup steps: [CONTRIBUTING.md § Cloudflare Pages deployment](CONTRIBUTING.md#cloudflare-pages-deployment).

## Making this repository public

The repository is prepared for public visibility:

- Deploy secrets are optional and only needed if you enable Cloudflare
- `LICENSE` and `SECURITY.md` are present
- `detect-secrets` baseline is enforced via pre-commit

A GitHub App token cannot change visibility. A repo admin should flip **Settings → General → Danger Zone → Change repository visibility → Public**.

## License

Build tooling and repository configuration are MIT — see [LICENSE](LICENSE). Wiki page content is mirrored from Servarr/Wiki.

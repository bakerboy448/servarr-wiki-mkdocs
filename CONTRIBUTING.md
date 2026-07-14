# Contributing to servarr-wiki-mkdocs

## Prefer upstream for content

Factual wiki corrections usually belong in [Servarr/Wiki](https://github.com/Servarr/Wiki). This repository mirrors that content into MkDocs Material.

Use this repo for:

- MkDocs / theme / navigation changes
- WikiJS → MkDocs conversion fixes (`scripts/wikijs_to_mkdocs.py`)
- Sync scripting and CI / deploy (GitHub Pages, Cloudflare Pages)

## Development setup

1. Install Python 3.10+ and pip
2. `make install` (creates `.venv/`, installs `requirements.txt`)
3. `make serve` — starts the local dev server
4. Open <http://localhost:8000> in your browser

Or run the underlying commands directly:

```bash
pip install -r requirements.txt
mkdocs serve
```

## Writing documentation

- Source pages live in `docs/` after conversion.
- Use [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) syntax.
- Admonitions use `!!! type` syntax (not WikiJS `{.is-*}` blockquotes).
- Tabs use `=== "Tab Title"` syntax.
- Icons use `:fontawesome-solid-icon-name:` syntax.

## Syncing upstream

```bash
git fetch upstream master
bash scripts/sync_upstream_wiki.sh upstream/master
mkdocs build
```

## Building

```bash
mkdocs build
```

Strict mode is intentionally off in `mkdocs.yml` until remaining broken-anchor debt is cleared.

## Issues and pull requests

Issue forms live under [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/):

| Template | Use when |
|----------|----------|
| Content bug | Incorrect / outdated / missing wiki text |
| Site / tooling bug | MkDocs, conversion, CI, Cloudflare |
| Feature / content request | New pages or tooling features |
| Upstream sync request | Ask for a Servarr/Wiki pull |

PRs use [`.github/pull_request_template.md`](.github/pull_request_template.md). Prefer small, focused diffs. Content syncs should note the upstream SHA.

## Cloudflare Pages deployment

Skeleton files:

- [`wrangler.toml`](wrangler.toml) — project name `servarr-wiki-mkdocs`, output `site/`
- [`.github/workflows/cloudflare-pages.yml`](.github/workflows/cloudflare-pages.yml) — build always; deploy gated
- [`cloudflare/README.md`](cloudflare/README.md) — short pointer + local smoke test

### 1. Create the Pages project

1. Cloudflare Dashboard → **Workers & Pages** → **Create** → **Pages** → **Direct Upload** (or connect later via Wrangler).
2. Project name must match `wrangler.toml`: `servarr-wiki-mkdocs`.
3. Optional: attach a custom domain under the project **Custom domains** tab.

Or from a machine with Wrangler:

```bash
npx --yes wrangler@4 pages project create servarr-wiki-mkdocs --production-branch=main
```

### 2. Create an API token

1. Cloudflare Dashboard → **My Profile** → **API Tokens** → **Create Token**.
2. Use the **Edit Cloudflare Workers** template (includes Pages), or a custom token with:
   - Account — Cloudflare Pages — Edit
   - Account — Account Settings — Read (if required by your plan/UI)
3. Scope the token to the target account.

### 3. Add GitHub secrets and the deploy gate

In the GitHub repo → **Settings** → **Secrets and variables** → **Actions**:

| Kind | Name | Value |
|------|------|--------|
| Secret | `CLOUDFLARE_API_TOKEN` | Token from step 2 |
| Secret | `CLOUDFLARE_ACCOUNT_ID` | Account ID (Workers & Pages overview / right sidebar) |
| Variable | `CF_PAGES_DEPLOY` | `true` to enable the deploy job |

Until `CF_PAGES_DEPLOY=true`, the workflow **builds** on push/PR but does **not** publish.

### 4. First deploy

- Push to `main`, or run **Actions → Cloudflare Pages → Run workflow**.
- Confirm the deployment in the Cloudflare Pages project **Deployments** tab.
- Update `site_url` in [`mkdocs.yml`](mkdocs.yml) if the production hostname is not GitHub Pages.

### 5. Local dry-run

```bash
pip install -r requirements.txt
mkdocs build
export CLOUDFLARE_API_TOKEN=...
export CLOUDFLARE_ACCOUNT_ID=...
npx --yes wrangler@4 pages deploy site --project-name=servarr-wiki-mkdocs
```

### Notes

- Build output directory is always `site/` (`mkdocs build`).
- GitHub Pages (`.github/workflows/gh-pages.yml`) is the primary production deploy and needs no secrets; Cloudflare is an optional second target, left disabled until you set `CF_PAGES_DEPLOY=true`.
- Do not commit API tokens. Rotate any token that was pasted into a shell history or chat log.

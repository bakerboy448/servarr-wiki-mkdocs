# Cloudflare Pages (skeleton)

This directory documents the Cloudflare Pages deployment path for the MkDocs
`site/` output. Configuration entrypoints:

| File | Role |
|------|------|
| [`../wrangler.toml`](../wrangler.toml) | Pages project name + `site` output dir |
| [`../.github/workflows/cloudflare-pages.yml`](../.github/workflows/cloudflare-pages.yml) | Build + deploy via Wrangler (needs secrets) |

Full setup steps live in [`../CONTRIBUTING.md`](../CONTRIBUTING.md#cloudflare-pages-deployment).

## Local deploy smoke test

```bash
pip install -r requirements.txt
mkdocs build
npx --yes wrangler@4 pages deploy site --project-name=servarr-wiki-mkdocs
```

Requires `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` in the environment.

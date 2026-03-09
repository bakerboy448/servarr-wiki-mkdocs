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

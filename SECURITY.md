# Security Policy

## Reporting a vulnerability

If you discover a security issue in this repository’s tooling, CI, or configuration, open a private GitHub security advisory on this repository or email the maintainer via the GitHub profile linked on the repo.

Do **not** open a public issue for credentials, tokens, or other secrets.

## Scope

- In scope: MkDocs config, GitHub Actions workflows, conversion/sync scripts, and accidental secret leakage in this repository.
- Out of scope: vulnerabilities in Lidarr/Radarr/Readarr/Sonarr/Whisparr/Prowlarr themselves — report those to the corresponding Servarr application repository.

## Public repository expectations

This project is intended to be public. Only `GITHUB_TOKEN` (provided by GitHub Actions) is used in workflows. Do not commit API keys, passwords, or private config.

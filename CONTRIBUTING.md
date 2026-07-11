# Contributing — RegLens HK

1. Read [`AGENTS.md`](AGENTS.md) before changing extraction, provenance, licensing,
   release, or public-site behaviour.
2. Use synthetic fixtures under `fixtures/synthetic/` only in Git.
3. Place real manually acquired documents in gitignored `private-data/`
   (see [`docs/PRIVATE_DATA.md`](docs/PRIVATE_DATA.md)).
4. Run **`make verify`** before opening a PR. That gate covers fixtures, ruff,
   mypy, pytest, Studio CI, `demo-release`, public-release scan, and site CI.
5. Do not add scrapers, real LLM network calls, OCR, NCHK, or semantic search
   without an explicit milestone approval.
6. Prefer deterministic parsing and schema-validated extraction with evidence spans.

## Two frontends

| Path | Name | Notes |
|------|------|-------|
| `apps/studio` | RegLens Studio | Internal. Cookie auth (fail-closed in production). Local data/seed. **Not** for Pages. |
| `apps/site` | RegLens Observatory | Public static site. Consumes publication release only. Deployed via `.github/workflows/pages.yml`. |

Do not merge Studio routes, API handlers, or middleware into `apps/site`.
Do not point Pages artifact upload at `apps/studio`.

## Publication changes

- Policy / taxonomy / schemas live under `publications/`.
- Release builder: `python -m reglens_worker release build` (see `make demo-release`).
- Changing `source_publication_policy` visibility is a licensing decision, not a
  convenience flag. Do not flip `internal_only` → public without counsel /
  consent-status progress recorded in the licensing audit.

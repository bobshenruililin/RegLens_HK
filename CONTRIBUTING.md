# Contributing — RegLens HK

1. Read [`AGENTS.md`](AGENTS.md) before changing extraction, provenance, licensing,
   release, or public-site behaviour.
2. Use synthetic fixtures under `fixtures/synthetic/` only in Git.
3. Place real manually acquired documents in gitignored `private-data/`
   (see [`docs/PRIVATE_DATA.md`](docs/PRIVATE_DATA.md)).
4. Run **`make verify`** before opening a PR. That gate covers fixtures, ruff,
   mypy, pytest, Studio CI, `demo-release`, public-release scan, and site CI
   (RC2 **demo mode** — no `DATABASE_URL` required).
5. For Postgres path changes, also run `make integration` /
   `make postgres-demo-pipeline` when `DATABASE_URL` is available (CI job
   `postgres-integration`).
6. RC3 source-sync work must follow [`docs/SOURCE_SYNC.md`](docs/SOURCE_SYNC.md)
   and [`docs/CRAWL_POLICY.md`](docs/CRAWL_POLICY.md): offline fixtures in
   ordinary CI, no PDF downloads, no CAPTCHA/auth bypass, and no public real
   release.
7. Public availability is not reuse permission; robots.txt is not a licence.
   MCHK remains internal-only, DCHK carries the July 14, 2018 caveat, and
   student-research letters do not unlock Pages.
8. Do not add scrapers, real LLM network calls, NCHK, semantic search, or public
   real-document publication without an explicit milestone and policy approval.
9. Prefer deterministic parsing and schema-validated extraction with evidence spans.
10. Prefer direct parameterized SQL (psycopg / `pg` client). Do not add an ORM
   without an ADR.

## Two frontends

| Path | Name | Notes |
|------|------|-------|
| `apps/studio` | RegLens Studio | Internal. Cookie auth (fail-closed in production). Local data/seed. **Not** for Pages. |
| `apps/site` | RegLens Observatory | Public static site. Consumes publication release only. Deployed via `.github/workflows/pages.yml`. |

Do not merge Studio routes, API handlers, or middleware into `apps/site`.
Do not point Pages artifact upload at `apps/studio`.

## Publication changes

- Policy / taxonomy / schemas live under `publications/`.
- Release builder:
  - Demo: `python -m reglens_worker release build --input-mode demo …`
  - Postgres: `python -m reglens_worker release build --input-mode postgres
    --publication-release-id <uuid> …`
- Changing `source_publication_policy` visibility is a licensing decision, not a
  convenience flag. Do not flip `internal_only` → public without counsel /
  consent-status progress recorded in the licensing audit.
- Privacy scans reduce risk but do not support a claim of complete
  de-identification.

## Storage modes (RC2)

- `REGLENS_MODE=demo` (default): filesystem artifacts under `data/`.
- `REGLENS_MODE=postgres`: PostgreSQL SoT; requires `DATABASE_URL` (fail closed).
  Do not mix demo seed decisions into postgres mode.

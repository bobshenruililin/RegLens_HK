# MVP-RC2 approval

## Approval

Approval was provided through the repository-owner implementation request
(Cursor Cloud agent task: “MVP-RC2 — RegLens Studio Trusted Data Plane”).

- Approver: repository owner (Shen Ruililin / bobshenruililin)
- Execution timestamp (UTC): 2026-07-11T13:45:00Z
- Branch: `cursor/mvp-rc2-trusted-data-plane`

## Approved RC2 scope

- Clean PostgreSQL operational schema and migration runner
- Explicit `REGLENS_MODE=demo|postgres` storage modes
- Content-addressed object store (local + optional MinIO/S3)
- Real job lease/retry worker path
- Immutable extracted propositions + append-only revisions
- Studio auth/roles (reviewer / publisher / admin)
- Trusted publication transaction feeding RC1 `publication_release.v1`
- PostgreSQL FTS for Studio (no pgvector)
- Observatory unchanged; Pages workflow preserved

## Continuing restrictions

No live crawl, OCR, real LLM, semantic search, NCHK, outcome prediction,
public full-text republication, Studio deployment to Pages, or breaking
changes to `publication_release.v1`. Consent/licensing statuses unchanged.

## Pre-production schema-reset approval (conditional)

A one-time clean migration baseline reset is approved because:

- no production `DATABASE_URL` is configured in this environment;
- no non-local persistent database is detected;
- no real decision corpus exists in a persistent DB;
- prior migrations (`001_init.sql`, `002_proposition_fts.sql`) are
  experimental development scaffolding only.

Under these conditions RC2 may replace the experimental schema with a clean
baseline (`packages/db/migrations/0001_rc2_baseline.sql`), archive prior
migration design notes, and require local Docker volumes to be recreated.

If a production/non-local database or real persistent corpus is later
detected, destructive reset must stop and report.

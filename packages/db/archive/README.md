# Experimental migrations archive

The files in this directory are **not** applied by the RC2 migration runner.

| File | Origin | Status |
|------|--------|--------|
| `001_init.experimental.sql` | Milestone 1 / experimental 2B scaffolding | Superseded |
| `002_proposition_fts.experimental.sql` | Experimental 2D FTS on `propositions` | Superseded |

## Why they were archived

Under `docs/approvals/MVP_RC2_APPROVAL.md`, a one-time pre-production schema
reset was approved because:

- no production `DATABASE_URL` was configured;
- no non-local persistent database was detected;
- no real decision corpus existed in a persistent DB;
- these migrations were experimental development scaffolding only.

## Replacement

The operational baseline is:

`packages/db/migrations/0001_rc2_baseline.sql`

That file replaces both experimental migrations with a clean RC2 schema
(content-addressed blobs, source collections, immutable extractions, append-only
proposition revisions, lease/retry jobs, Studio auth, publication releases).
It does **not** include pgvector or an embeddings table.

## Operator note

Local Docker Postgres volumes created against `001`/`002` must be **recreated**
before applying `0001_rc2_baseline.sql`. Do not attempt an in-place upgrade from
the experimental schema.

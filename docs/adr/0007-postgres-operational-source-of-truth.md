# ADR 0007 — PostgreSQL as operational source of truth

## Status

Accepted (MVP-RC2)

## Context

MVP-RC1 delivered Observatory from filesystem seed artifacts and a frozen
`publication_release.v1` bundle. Studio still leaned on local `data/` JSON and
experimental 2B–2D Postgres scaffolding (`001_init` / `002_proposition_fts`),
which mixed pgvector intentions with a mutable proposition review model.

RC2 requires a trusted Studio data plane: content-addressed blobs, real job
leases, immutable extractions with append-only revisions, role-based auth, and a
publication transaction that feeds the unchanged RC1 release contract.

## Decision

PostgreSQL is the **operational source of truth** for RegLens Studio when
`REGLENS_MODE=postgres`:

- Baseline migration: `packages/db/migrations/0001_rc2_baseline.sql`
- Experimental `001`/`002` archived under `packages/db/archive/` (reset approved)
- No pgvector / embeddings; Studio search uses `tsvector` FTS
- `REGLENS_MODE=demo` may still use filesystem stores for synthetic demos
- Observatory and Pages continue to consume only checked publication bundles —
  never raw Postgres rows

## Consequences

- Local volumes built on experimental migrations must be recreated.
- Application repositories replace ad-hoc `db.py` upserts.
- Publication remains a deliberate transaction; `publication_release.v1` stays frozen.
- Destructive reset is forbidden if a production/non-local corpus appears later.

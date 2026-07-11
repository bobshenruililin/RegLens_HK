# Database migrations (MVP-RC2)

## Source of truth

| Path | Role |
|------|------|
| `packages/db/migrations/*.sql` | Applied by `python -m reglens_worker db migrate` |
| `packages/db/archive/` | Historical experimental 001/002 — **not** applied |

Baseline file: `0001_rc2_baseline.sql` (no pgvector).

## Apply

```bash
export DATABASE_URL=postgresql://reglens:reglens_local_only@127.0.0.1:5432/reglens
export REGLENS_MODE=postgres
make db-migrate
# equivalent: python -m reglens_worker db migrate
make db-status
```

The runner records filenames + SHA-256 checksums in `schema_migrations`.
Checksum mismatch → fail closed (do not silently re-apply).

## Mounts are not enough

`docker-compose.yml` does **not** mount migration SQL into
`/docker-entrypoint-initdb.d` as the schema path. Even if init scripts run on
first volume create, **always** run `make db-migrate` after bringing Postgres up.
Application code and CI assume the runner’s bookkeeping table.

## Reset (local only)

```bash
make db-reset-local   # asserts local host via assert_local_database_url
make db-migrate
```

Remote / production hosts are rejected. Recreate Compose volumes when moving
from archived experimental migrations to the RC2 baseline.

## ADR

See [`adr/0007-postgres-operational-source-of-truth.md`](adr/0007-postgres-operational-source-of-truth.md).

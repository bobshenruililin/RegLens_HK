# Backup and restore (MVP-RC2)

Guidance for **local / pre-production** Postgres and object storage. Not a
managed-cloud SLA.

## What to back up

| Asset | Why |
|-------|-----|
| PostgreSQL database | Operational SoT: decisions, revisions, reviews, jobs, auth |
| Object store (`DATA_ROOT/objects` or MinIO bucket) | Immutable document bytes keyed by SHA-256 |
| Publication release bundles | Frozen public artifacts under `generated/` |

Do **not** treat Studio session cookies or `.env` passwords as backup targets
worth retaining in the same archive as corpora.

## Logical dump (local)

```bash
export DATABASE_URL=postgresql://reglens:reglens_local_only@127.0.0.1:5432/reglens
pg_dump "$DATABASE_URL" --format=custom -f reglens.dump
# restore into an empty local DB only:
pg_restore --clean --if-exists -d "$DATABASE_URL" reglens.dump
make db-status
```

After restore, confirm migration checksums still match
`packages/db/migrations/*.sql`. Prefer restore → migrate (no-op) over editing
SQL on a live dump.

## Object store

- **Local:** copy `data/objects/` (content-addressed).
- **MinIO:** `mc mirror` the bucket; keys must match `blobs.storage_key`.

Mismatched DB rows vs missing blobs will fail worker verification.

## Publication bundles

Versioned directories under `generated/public-release*` are rebuildable from an
approved Postgres release (`build_release_from_postgres`) or demo filesystem
seed. Keep approved release rows + object bytes if you need bit-identical
regeneration.

## Destructive reset vs restore

`make db-reset-local` is for wiping local demos, not recovery. Use dumps for
restore. See [`OPERATIONS.md`](OPERATIONS.md).

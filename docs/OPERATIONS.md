# Operations (MVP-RC2)

Day-2 notes for local and CI RegLens HK. Not a production runbook.

## Storage modes

- **`REGLENS_MODE=demo`** — filesystem artifacts under `DATA_ROOT` (default `data/`).
  Used by `make verify` without Postgres.
- **`REGLENS_MODE=postgres`** — PostgreSQL is operational SoT; object store holds
  immutable bytes. Requires `DATABASE_URL`.

## Compose

```bash
make db-up          # postgres:16 + MinIO (local-only credentials)
make db-migrate     # REQUIRED — volume mounts do not apply RC2 migrations
make db-status
make db-down
```

Destructive local reset (prints warning; asserts local DSN):

```bash
export DATABASE_URL=postgresql://reglens:reglens_local_only@127.0.0.1:5432/reglens
make db-reset-local
make db-migrate
```

If **Docker is unavailable**, `db-reset-local` falls back to `psql` DROP/CREATE
against a local URL, or exits with docs. Prefer Docker so volumes match Compose.

## Worker

```bash
make demo-enqueue          # enqueue fixtures/manifests/m1.jsonl
make worker-once           # claim/process one job
# or:
python -m reglens_worker worker run --data-root data
```

Postgres path: set `REGLENS_MODE=postgres` and `DATABASE_URL` first.

## Synthetic Postgres demo

```bash
export REGLENS_MODE=postgres DATABASE_URL=...
make postgres-demo-pipeline   # migrate → admin → enqueue → drain → demo accept → release
make postgres-demo-release    # public-scan on generated/public-release-pg
make site-build-from-postgres-release
```

The pipeline **rejects** any `fixture_kind=real`. Auto-accept is labelled
**DEMO ONLY** and applies only to synthetic revisions.

## CI

- `python` / `studio` / `site` jobs — demo-mode RC1 gate (no DATABASE_URL).
- `postgres-integration` — Postgres 16 service, migrate, integration tests,
  demo pipeline or vertical-slice fallback.
- `source-health` — manual `workflow_dispatch` only, skipped on forks,
  metadata-only, offline fixture parser summary artifact; it does **not**
  download PDFs and is not scheduled.

## RC3 source/pilot commands

```bash
make rc3-verify
make sources-status
make source-sync-mchk-dry
make source-sync-dchk-dry
make core50-status
make extraction-eval
```

RC3 live-source work remains policy-gated. Public availability is not reuse
permission; robots.txt is not a licence; MCHK remains internal-only; DCHK carries
the July 14, 2018 caveat; student-research letters do not unlock Pages; and no
public real release or complete de-identification claim is made.

## Credentials

Compose defaults (`reglens` / `reglens_local_only`) are **local-only**. Optional
separate worker/studio/publisher DB users are documented as comments in
`docker-compose.yml` — wire via `.env` when hardening beyond demos.

## Related

- [`DATABASE_MIGRATIONS.md`](DATABASE_MIGRATIONS.md)
- [`BACKUP_RESTORE.md`](BACKUP_RESTORE.md)
- [`THREAT_MODEL.md`](THREAT_MODEL.md)
- [`SOURCE_SYNC.md`](SOURCE_SYNC.md)
- [`CRAWL_POLICY.md`](CRAWL_POLICY.md)

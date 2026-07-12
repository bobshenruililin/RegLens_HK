# Local setup — MVP-RC1 / RC2

## Baseline restrictions

Internal/non-commercial for real corpora; no crawl; no real LLM; no OCR in the
default path; no semantic search; no NCHK; no real documents in Git; no Pages
deploy of Studio; real `public` release blocked while policy is `internal_only`.

## Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r services/worker/requirements.txt
# optional LawTrace sibling package (needed for tests/lawtrace):
# pip install -r services/lawtrace-worker/requirements.txt
# optional lock refresh: make lock
export PYTHONPATH=services/worker
# LawTrace tests also resolve via tests/lawtrace/conftest.py
```

## Make targets (preferred)

### Demo mode (no DATABASE_URL) — RC2 verify gate

| Target | What it does |
|--------|----------------|
| `make demo-ingest` | Reset `data/`, ingest `fixtures/manifests/m1.jsonl` with `--demo-auto-approve-synthetic` |
| `make demo-enqueue` | Enqueue manifest jobs only |
| `make worker-once` | Claim/process one job (demo auto-approve synthetic) |
| `make demo-release` | `demo-ingest` + `release build` → `generated/public-release` + public-scan |
| `make pages-artifact` | Copy release into `apps/site/public/data/release/` (+ `.nojekyll`) |
| `make studio-dev` | `cd apps/studio && npm run dev` |
| `make site-dev` | `cd apps/site && npm run dev` |
| `make site-build` | `pages-artifact` + Observatory production build |
| `make verify` | Full **demo-mode** gate (fixtures, lint, types, tests, studio-ci, demo-release, public-scan, site-ci) |
| `make public-scan` | Re-run `scripts/check_public_release.py` on `generated/public-release` |

### Postgres mode (RC2)

| Target | What it does |
|--------|----------------|
| `make db-up` / `db-down` | Compose Postgres 16 + MinIO |
| `make db-migrate` / `db-status` | Apply / list SQL migrations (**required** after up) |
| `make db-reset-local` | Destructive local wipe (warns; asserts local DSN) |
| `make integration` | `pytest -m integration` (+ pg tests); skips locally if no DSN; **fails in CI** if unset |
| `make postgres-demo-pipeline` | Synthetic-only Postgres vertical demo → `generated/public-release-pg` |
| `make postgres-demo-release` | Public-scan on Postgres demo bundle |
| `make site-build-from-postgres-release` | Observatory build from `public-release-pg` |
| `make rc2-acceptance` | `verify` + postgres acceptance when `DATABASE_URL` set |

## Ingest (default: pending / unpublished)

```bash
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl --data-root data
```

Synthetic demo auto-approve (rejects non-synthetic rows):

```bash
make demo-ingest
```

## Postgres local stack

```bash
make db-up
export DATABASE_URL=postgresql://reglens:reglens_local_only@127.0.0.1:5432/reglens
export REGLENS_MODE=postgres
make db-migrate   # mounts alone are NOT enough — see docs/DATABASE_MIGRATIONS.md
```

If Docker is unavailable, see [`OPERATIONS.md`](OPERATIONS.md) for `psql`-based
reset notes. Recreate volumes after leaving the archived pgvector/experimental
migrations.

## Frontends

### Studio (internal) — `apps/studio`

```bash
make studio-dev
```

See [`STUDIO.md`](STUDIO.md). Production auth is fail-closed. **Do not** deploy
to GitHub Pages.

### Observatory (public) — `apps/site`

```bash
make pages-artifact
make site-dev
```

Optional Pages base path: `NEXT_PUBLIC_BASE_PATH` (e.g. `/RegLens_HK`).

## Private data

See [`PRIVATE_DATA.md`](PRIVATE_DATA.md). The `private-data/` tree is gitignored.

## Docs

- [`OPERATIONS.md`](OPERATIONS.md) — workers, Compose, CI
- [`DATABASE_MIGRATIONS.md`](DATABASE_MIGRATIONS.md)
- [`BACKUP_RESTORE.md`](BACKUP_RESTORE.md)
- [`REVIEW_WORKFLOW.md`](REVIEW_WORKFLOW.md)

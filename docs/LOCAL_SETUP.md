# Local setup — MVP-RC1

## Baseline restrictions

Internal/non-commercial for real corpora; no crawl; no real LLM; no OCR in the
default path; no semantic search; no NCHK; no real documents in Git; no Pages
deploy of Studio; real `public` release blocked while policy is `internal_only`.

## Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r services/worker/requirements.txt
# optional lock refresh: make lock
export PYTHONPATH=services/worker
```

## Make targets (preferred)

| Target | What it does |
|--------|----------------|
| `make demo-ingest` | Reset `data/`, ingest `fixtures/manifests/m1.jsonl` with `--demo-auto-approve-synthetic` |
| `make demo-release` | `demo-ingest` + `release build` → `generated/public-release` + public-scan |
| `make pages-artifact` | Copy release into `apps/site/public/data/release/` (+ `.nojekyll`) |
| `make studio-dev` | `cd apps/studio && npm run dev` |
| `make site-dev` | `cd apps/site && npm run dev` |
| `make site-build` | `pages-artifact` + Observatory production build |
| `make verify` | Full RC1 gate (fixtures, lint, types, tests, studio-ci, demo-release, public-scan, site-ci) |
| `make public-scan` | Re-run `scripts/check_public_release.py` on `generated/public-release` |

## Ingest (default: pending / unpublished)

```bash
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl --data-root data
```

Synthetic demo auto-approve (rejects non-synthetic rows):

```bash
make demo-ingest
# or:
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl \
  --data-root data --demo-auto-approve-synthetic
```

Immutable audit artifacts: `data/meta/runs/<run_key>/extraction.json` (+ `.sha256`).
Reviewed decisions for release: `data/seed/decisions/`.

## Release build

```bash
make demo-release
```

Equivalent manual invocation is in the root `Makefile` (`demo-release` target):
annotations, policy, taxonomy under `publications/`, `release_mode=synthetic_demo`.

## Frontends

### Studio (internal) — `apps/studio`

```bash
cd apps/studio
npm ci
npm run typecheck
npm run build
npm run dev
# or: make studio-dev
```

Production auth is fail-closed: set `AUTH_PASSWORD` and `REGLENS_SESSION_SECRET`
when `NODE_ENV=production`. Dev defaults exist only outside production.

**Do not** configure this app for GitHub Pages.

### Observatory (public) — `apps/site`

```bash
make pages-artifact   # requires demo-release output
cd apps/site
npm ci
npm run typecheck
npm run build
npm run dev
# or: make site-dev
```

Optional Pages base path: `NEXT_PUBLIC_BASE_PATH` (e.g. `/RegLens_HK`).

## Private data

See [`PRIVATE_DATA.md`](PRIVATE_DATA.md). The `private-data/` tree is gitignored.

## Compose (optional; local-only credentials)

```bash
docker compose config   # validate file
docker compose up -d db minio
```

Postgres/MinIO are **not** required for synthetic demo ingest, release build, or
Observatory static export.

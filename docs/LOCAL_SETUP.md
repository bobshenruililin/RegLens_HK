# Local setup — Milestone 2A

## Baseline restrictions

Internal/non-commercial; no crawl; no real LLM; no OCR; no semantic search; no NCHK;
no real documents in Git.

## Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r services/worker/requirements.txt
# optional lock refresh: make lock
export PYTHONPATH=services/worker
```

## Ingest (default: pending / unpublished)

```bash
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl --data-root data
```

Synthetic demo auto-approve (rejects non-synthetic rows):

```bash
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl --data-root data --demo-auto-approve-synthetic
```

Immutable audit artifacts: `data/meta/runs/<run_key>/extraction.json` (+ `.sha256`).
Demo pointer only: `data/seed/decision.json`.

## Verify everything

```bash
make verify
```

## Web

```bash
cd apps/web
npm ci
npm run typecheck
npm run build
npm run dev
```

## Private data

See `docs/PRIVATE_DATA.md`. The `private-data/` tree is gitignored.

## Compose (optional; local-only credentials)

```bash
docker compose config   # validate file
docker compose up -d db minio
```

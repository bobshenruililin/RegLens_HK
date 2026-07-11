# Local setup — Milestone 1

## Prerequisites

- Python 3.11+ (3.12 tested)
- Node.js 20+ and npm
- Optional: Docker + Docker Compose for Postgres/pgvector and MinIO

## 1. Clone and enter the repo

```bash
cd /path/to/reglens-hk
```

## 2. Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r services/worker/requirements.txt
export PYTHONPATH=services/worker
```

## 3. Ingest fixtures

Synthetic fixtures ship under `fixtures/raw/`. They are **not** official judgments.

```bash
python -m reglens_worker ingest \
  --manifest fixtures/manifests/m1.jsonl \
  --data-root data
```

Idempotent re-run (same SHA-256 → no duplicate blobs):

```bash
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl
```

Hash a single file:

```bash
python -m reglens_worker hash fixtures/raw/mchk/SYN-MCHK-2024-001.html
```

Hash all manifest rows:

```bash
python scripts/hash_manifest.py fixtures/manifests/m1.jsonl
```

Outputs:

- `data/objects/sha256/…` — immutable raw bytes
- `data/meta/documents|spans|extractions…` — JSON metadata
- `data/seed/decision.json` — demo decision for the web UI
- `data/seed/decisions/<id>.json` — per-decision seed

## 4. Tests

```bash
source .venv/bin/activate
export PYTHONPATH=services/worker
pytest
```

## 5. Web application

```bash
cd apps/web
npm install
npm run dev
```

Open:

- http://localhost:3000 — index with link to seeded decision
- http://localhost:3000/decisions/<id> — source-linked decision detail

Production-style run:

```bash
cd apps/web
npm run build
npm start
```

## 6. Optional: Postgres + MinIO

```bash
cp .env.example .env
docker compose up -d db minio
```

- Postgres: `postgresql://reglens:reglens@localhost:5432/reglens`
- MinIO API: http://localhost:9000 (user `reglens` / `reglenssecret`)
- MinIO console: http://localhost:9001
- Migration applied from `packages/db/migrations/001_init.sql` on first boot

Milestone 1 worker uses the **local filesystem store** by default even when
Compose is running. DB wiring lands in a later milestone.

## 7. Manual real fixtures (optional)

Follow `scripts/download_checklist.md`. Do not scrape. Update the licensing
audit before any non-synthetic material is committed or redistributed.

## 8. What is intentionally missing

- Live source adapters / crawlers
- Real LLM provider network calls
- Human review queue UI (propositions are auto-accepted only for synthetic demo seeds)
- Semantic search / pgvector queries in the UI

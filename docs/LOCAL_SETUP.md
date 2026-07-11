# Local setup — MVP Backbone

## Prerequisites

- Python 3.12+
- Node.js 20+
- Optional: Docker Compose for Postgres/pgvector + MinIO

## Restrictions (still in force)

- Internal / non-commercial
- No live crawling
- No public real-document republication
- Mock LLM only
- No NCHK
- No semantic search

## 1. Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r services/worker/requirements.txt
export PYTHONPATH=services/worker
```

## 2. Ingest fixtures (pending review by default)

```bash
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl --data-root data
python -m reglens_worker jobs list --data-root data
python -m reglens_worker review list --data-root data
```

Auto-accept synthetic demo only:

```bash
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl --data-root data --accept
```

## 3. Tests

```bash
pytest
```

## 4. Web (auth-gated)

```bash
cd apps/web
npm install
# optional: export AUTH_PASSWORD=... REGLENS_SESSION_SECRET=...
npm run dev
```

Open http://localhost:3000 — password default `reglens-internal`.

## 5. Optional Compose

```bash
docker compose up -d db minio
export DATABASE_URL=postgresql://reglens:reglens@localhost:5432/reglens
export OBJECT_STORE=minio
# apply migrations 001 then 002
psql "$DATABASE_URL" -f packages/db/migrations/001_init.sql
psql "$DATABASE_URL" -f packages/db/migrations/002_proposition_fts.sql
```

## 6. Search CLI

```bash
python -m reglens_worker search "misconduct" --data-root data --regulator MCHK
```

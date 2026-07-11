# RegLens HK

Evidence-linked database and analysis platform for Hong Kong regulatory and
professional disciplinary decisions. Milestone 1 focuses on **fixture ingest**,
**immutable hashing**, **page segmentation**, **strict extraction schemas**, a
**mock LLM provider**, and one **source-linked decision detail page**.

This is an internal research tool. It does **not** provide legal advice.

## Milestone 1 scope

- Manual fixtures only (no live crawling)
- Mock LLM only (no real LLM network calls)
- PostgreSQL migrations + local filesystem artifact store
- Unit tests for parsers, schemas, and provenance links

Read [AGENTS.md](AGENTS.md) before changing extraction or provenance behaviour.

## Quick start (host tools; no Docker required for demo)

```bash
# 1) Python deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r services/worker/requirements.txt

# 2) Ingest synthetic fixtures (idempotent)
export PYTHONPATH=services/worker
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl --data-root data

# 3) Run tests
pytest

# 4) Web UI
cd apps/web
npm install
npm run dev
# open http://localhost:3000 and follow the decision link
```

Full command reference: [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md).

## Optional Docker services

```bash
docker compose up -d db minio
# applies packages/db/migrations/001_init.sql on first boot
```

## Repository layout

See Phase 0 docs under `docs/` and the tree in `docs/ARCHITECTURE.md`.

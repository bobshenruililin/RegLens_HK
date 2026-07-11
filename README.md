# RegLens HK

Evidence-linked database and analysis platform for Hong Kong regulatory and
professional disciplinary decisions.

**MVP Backbone (2A–2D)** is approved and implemented: contracts, determinism,
private-data boundary, CI, Postgres/object-store/jobs interfaces, auth-gated
review/publication, and keyword FTS with evidence UX.

This is an internal research tool. It does **not** provide legal advice.

## Restrictions

- Internal / non-commercial
- No live crawling
- No public real-document republication
- Mock LLM only (no real LLM without privacy approval)
- No NCHK
- No semantic search before FTS evaluation

Read [AGENTS.md](AGENTS.md). Phase 0 package: [docs/README.md](docs/README.md).
Backbone notes: [docs/MVP_BACKBONE.md](docs/MVP_BACKBONE.md).

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/worker/requirements.txt
export PYTHONPATH=services/worker
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl --data-root data --accept
pytest
cd apps/web && npm install && npm run dev
# http://localhost:3000  password: reglens-internal
```

Full commands: [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md).

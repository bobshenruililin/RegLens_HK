# RegLens HK

Evidence-linked database for Hong Kong regulatory disciplinary decisions
(internal / non-commercial research tool — not legal advice).

## Milestone 2A

Trusted contracts (extraction v2), deterministic immutable runs, synthetic vs
private-data boundary, parser safety, and CI.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/worker/requirements.txt
export PYTHONPATH=services/worker
python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl --data-root data
# optional synthetic demo publish only:
# python -m reglens_worker ingest --manifest fixtures/manifests/m1.jsonl --data-root data --demo-auto-approve-synthetic
make verify
cd apps/web && npm ci && npm run dev
```

See [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md), [AGENTS.md](AGENTS.md), and [docs/README.md](docs/README.md).

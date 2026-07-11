# Architecture (Milestone 1)

```text
fixtures/manifests/*.jsonl
        │
        ▼
reglens_worker ingest ──► data/objects (immutable SHA-256 blobs)
        │                 data/meta (documents, spans, extractions)
        │                 data/seed (decision JSON for UI)
        ▼
MockLLMProvider (offline heuristics)
        │
        ▼
JSON Schema + quote alignment
        │
        ▼
Next.js decision detail page  (/decisions/[id])
```

Optional Compose services: Postgres/pgvector + MinIO (see `docker-compose.yml`).

## Repository tree

```text
reglens-hk/
  AGENTS.md
  README.md
  LICENSE
  docker-compose.yml
  .env.example
  docs/
  fixtures/
  apps/web/
  services/worker/reglens_worker/
  packages/db/migrations/
  packages/extraction-schema/
  scripts/
  tests/
  data/   # generated locally; gitignored contents
```

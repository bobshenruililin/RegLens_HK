# System architecture (Milestone 2A)

```mermaid
flowchart TB
  Fixtures[Synthetic fixtures and manifest]
  Ingest[Ingest hash segment]
  Extract[Mock LLM provider v2]
  Val[JSON Schema and domain invariants]
  Runs[Immutable run store meta/runs/run_key]
  Pointer[Mutable demo pointer seed]
  Web[Next.js decision page]

  Fixtures --> Ingest --> Extract --> Val --> Runs
  Runs --> Pointer --> Web
```

## Milestone 2A focus

Trusted contracts, deterministic immutable artifacts, synthetic/private-data boundary, and CI.
PostgreSQL persistence, MinIO wiring, authentication, review UI, and search are **out of scope** for 2A (see Milestone 2B+).

## Design notes

- Documents are untrusted data.
- Mock provider only; no network LLM calls.
- Atomic writes; run-key conflicts quarantine differing outputs.
- Compose file remains for local infra prep; image tags are pinned; credentials labelled local-only.

# Six-week milestone plan

| Week | Outcome | Exit criteria |
|------|---------|---------------|
| **W1 — Foundations & licence gate** | Repo, Compose, migrations, audit, fixture ingest | Licence rows completed; immutable ingest idempotent |
| **MVP Backbone 2A** | Contracts, determinism, private-data boundary, CI | Shared contracts; deterministic IDs; PII redaction tests; CI green |
| **MVP Backbone 2B** | PostgreSQL, object storage, jobs | Idempotent jobs; blob store interface; DB persistence path |
| **MVP Backbone 2C** | Review, publication, authentication | Auth-gated app; publish requires spans + review |
| **MVP Backbone 2D** | FTS search and evidence UX | Keyword FTS + filters; quote highlight on decision page |
| **Later** | OCR hardening, richer extraction, gold eval | Separate approvals; no semantic search until FTS evaluated |

## Status

| Item | Status |
|------|--------|
| W1 | Done (PR #1) |
| Phase 0 docs | Done (PR #2) |
| MVP Backbone 2A–2D | Approved 2026-07-11 — this delivery |
| Semantic search / real LLM / live crawl / NCHK | Blocked |

See [`approvals/MVP_BACKBONE_APPROVAL.md`](approvals/MVP_BACKBONE_APPROVAL.md).

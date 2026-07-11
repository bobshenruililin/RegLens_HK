# Relational schema

Canonical SQL: [`packages/db/migrations/001_init.sql`](../packages/db/migrations/001_init.sql).

## Entities

- `regulators`, `sources`
- `documents` (immutable SHA-256 + storage_key)
- `document_spans` (page-level provenance units + `tsvector`)
- `practitioners`, `decisions`, `decision_practitioners`
- `extraction_runs`, `propositions`, `proposition_spans`
- `embeddings` (pgvector; unused in M1 UI)
- `jobs`, `audit_events`, `review_queue_items`, `coverage_warnings`

## Integrity rules

1. Re-ingest of the same SHA-256 is a no-op for blob storage.
2. `propositions.published` requires `review_status IN ('accepted','edited')`.
3. Application + tests require ≥1 `proposition_spans` / evidence span before publish.
4. Raw bytes are never updated in place.

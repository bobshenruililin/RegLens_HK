# Relational schema

Canonical migration: [`packages/db/migrations/001_init.sql`](../packages/db/migrations/001_init.sql).

## Entity overview

```text
regulators(id, code, name, homepage_url, created_at)
sources(id, regulator_id, source_id, index_url, licence_status, terms_reviewed_at, notes)
documents(
  id, source_id, external_ref, title, decision_date, hearing_dates[],
  language, mime_type, byte_size, sha256, storage_key,
  ingest_status, text_quality, ocr_used, created_at, immutable
)
document_versions(id, document_id, sha256, storage_key, acquired_at, note)
document_spans(
  id, document_id, page_no, span_type,  -- page|block|paragraph
  char_start, char_end, text, text_hash, bbox_json, text_tsv, created_at
)
practitioners(
  id, regulator_id, registration_no, display_name, profession, normalized_name
)
decisions(
  id, document_id, regulator_id, case_ref, decision_date,
  profession, appeal_status_as_stated, published_at, coverage_json
)
decision_practitioners(decision_id, practitioner_id, role)

extraction_runs(
  id, document_id, pipeline_version, model_provider, model_version,
  prompt_version, started_at, finished_at, status, input_hash
)
propositions(
  id, decision_id, extraction_run_id,
  prop_type, epistemic_class, claim_text, structured_json, confidence,
  review_status, reviewed_by, reviewed_at, published
)
proposition_spans(proposition_id, span_id, quote_text, relevance)

embeddings(id, owner_type, owner_id, model, dims, embedding vector, created_at)
jobs(id, job_type, dedupe_key, payload_json, status, attempts,
     last_error, created_at, updated_at, started_at, finished_at)
audit_events(id, actor, action, entity_type, entity_id, before_json, after_json, at)
review_queue_items(id, proposition_id, decision_id, priority, reason, status)
coverage_warnings(id, decision_id, code, message, severity, active)
```

## Integrity rules

1. `documents.sha256` uniquely identifies content; re-ingest of the same hash is a no-op for the blob.
2. `propositions.published = true` only if `review_status IN ('accepted', 'edited')` **and** ≥1 supporting span/evidence row exists (DB check + application/tests).
3. Raw document bytes are never updated in place; replacement = new version row + new hash.
4. Seeded MVP regulators/sources: `MCHK` / `mchk_judgments`, `DCHK` / `dchk_judgments` with `licence_status=internal_use_only`.

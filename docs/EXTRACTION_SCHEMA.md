# Extraction JSON Schema

Source of truth: [`packages/extraction-schema/extraction_result.v1.json`](../packages/extraction-schema/extraction_result.v1.json).

## Rules

- `schema_version` must be `1.0.0`
- Every proposition needs `evidence[]` with `page_no` + `quote`
- `legal_test` ⇒ `epistemic_class` must be `interpretation`
- Post-validation: quotes must align to page span text
- Invalid payloads are rejected; never auto-published

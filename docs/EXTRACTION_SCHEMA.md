# Extraction JSON Schema

## Current contract (v2)

Source of truth: [`packages/extraction-schema/extraction_result.v2.json`](../packages/extraction-schema/extraction_result.v2.json).

| Rule | Detail |
|------|--------|
| Version | `schema_version` = `2.0.0` |
| Identity | Providers emit `client_ref` only — **no** database UUIDs |
| Required | `decision_metadata`, `coverage`, `propositions` |
| Case refs | `decision_metadata.case_refs` array |
| Dates | typed: inquiry, judgment, publication, conduct, order_effective (`format: date`) |
| Derivation | `verbatim` \| `normalized` \| `inferred` |
| Epistemic | `fact` \| `interpretation` (`legal_test` ⇒ interpretation) |
| Relations | by `client_ref` (finding_resolves_charge, sanction_applies_to_charge, rule_governs_charge, authority_supports_legal_test, factor_affects_sanction) |
| Evidence | `page_no` + `quote`; `span_id` required after resolution; offsets only as a pair with `char_end >= char_start` |
| Additional properties | rejected |

## Domain invariants

Implemented in `reglens_worker.schema_validate.domain_validate_extraction` with an explicit JSON Schema `FormatChecker` for dates.

## Migration from v1

`migrate_v1_to_v2()` maps `case_ref`/`decision_date`/`id` → `case_refs`/`dates.judgment`/`client_ref`. v1 schema file is retained for validation of legacy fixtures.

## Post-validation

Missing or mismatched evidence fails validation — the mock provider does **not** substitute the first line of a page.

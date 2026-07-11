# Extraction JSON Schema

Source of truth: [`packages/extraction-schema/extraction_result.v1.json`](../packages/extraction-schema/extraction_result.v1.json).

Validated in Python with `jsonschema` (Draft 2020-12) before any persistence of extraction output.

## Design rules

| Rule | Detail |
|------|--------|
| Version pin | `schema_version` must be `"1.0.0"` |
| Document binding | `document_sha256` must be 64 lowercase hex chars |
| Extractor audit | `pipeline_version`, `model_provider`, `model_version`, `prompt_version` required |
| Evidence mandatory | Every proposition has `evidence` with `minItems: 1` (`page_no` + `quote`) |
| Epistemic split | `epistemic_class` ∈ {`fact`, `interpretation`} |
| Legal tests | If `prop_type=legal_test` then `epistemic_class` **must** be `interpretation` |
| Prop types | charge, rule, finding, legal_test, aggravating_factor, mitigating_factor, sanction, costs, authority, appeal_status |
| Regulators (MVP) | `decision_metadata.regulator_code` ∈ {`MCHK`, `DCHK`} |
| Professions (MVP) | `doctor`, `dentist` |

## Post-validation (application layer)

Every `evidence.quote` must exact- or whitespace-collapsed-match the corresponding page span text. Failures quarantine the proposition — never auto-publish.

## Conceptual shape

```json
{
  "schema_version": "1.0.0",
  "document_sha256": "<64-hex>",
  "extractor": {
    "pipeline_version": "...",
    "model_provider": "...",
    "model_version": "...",
    "prompt_version": "..."
  },
  "decision_metadata": {
    "case_ref": null,
    "decision_date": "YYYY-MM-DD",
    "regulator_code": "MCHK",
    "profession": "doctor",
    "defendant_registration_no": null,
    "defendant_name_as_published": null
  },
  "propositions": [
    {
      "id": "<uuid>",
      "prop_type": "charge",
      "epistemic_class": "fact",
      "claim_text": "...",
      "structured": null,
      "confidence": 0.0,
      "evidence": [
        { "span_id": null, "page_no": 1, "quote": "...", "char_start": 0, "char_end": 10 }
      ]
    }
  ],
  "coverage": { "missing_fields": [], "warnings": [] }
}
```

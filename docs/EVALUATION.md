# Gold-standard evaluation methodology

## 1. Gold corpus

15–20 decisions (mix MCHK/DCHK, digital + scanned, guilty/mixed sanctions, multi-charge). Store under `fixtures/gold/` with annotation JSON conforming to `extraction_result.v1.json`.

## 2. Double annotation

Two humans label propositions + page/quote evidence using the JSON schema. An adjudicator resolves disagreements. Record annotator ids and adjudication notes in the gold manifest.

## 3. Extraction metrics

| Metric | Definition |
|--------|------------|
| Field precision / recall | Per `prop_type` bucket (charges, sanctions, rules, authorities, …) |
| Evidence support rate | % predicted propositions whose quote is substring / whitespace-collapsed match of span text |
| Orphan rate | Propositions failing evidence checks (must be ~0 after validation layer) |
| Legal-test contamination | % of `fact` labels that should be `interpretation` (manual audit) |

## 4. Search metrics

- nDCG@10 on 20 keyword queries
- Qualitative check on 10 semantic queries (when semantic search is enabled)

## 5. Provenance UX test

For 10 random published fields, a reviewer can open the correct page in ≤2 clicks.

## 6. Regression

- Gold fixtures run in CI on parser + schema + quote-align.
- LLM judged only in a scheduled eval job with pinned model/prompt versions.

## 7. Pass bar for MVP demo

- Evidence support ≥95% on auto-validated output
- Published-set precision ≥90% after human review on gold

## Milestone 1 automated gates (current)

Already enforced in unit tests:

- Schema validation errors = 0 on mock outputs for synthetic fixtures
- Evidence support rate = 100% after quote alignment
- Every published proposition resolves to a page span id

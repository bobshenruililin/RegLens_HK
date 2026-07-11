# Gold-standard evaluation methodology

## 1. Gold corpus

15–20 decisions (mix MCHK/DCHK, digital + scanned, guilty/mixed sanctions, multi-charge). Store under `fixtures/gold/` with annotation JSON conforming to `extraction_result.v1.json` (migrate to v2 where applicable).

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

- nDCG@10 on 20 keyword queries (Studio / FTS path when enabled)
- Qualitative check on 10 semantic queries (when semantic search is enabled — not RC1)

Observatory client-side explore is **not** scored as retrieval quality for the
regulator population; it only exercises filter UX over the release catalog.

## 5. Provenance UX test

For 10 random published fields, a reviewer can open the correct page in ≤2 clicks
(Studio / internal evidence view).

## 6. Regression

- Gold fixtures run in CI on parser + schema + quote-align.
- LLM judged only in a scheduled eval job with pinned model/prompt versions.
- Public release: `scripts/check_public_release.py` + Pages workflow artifact guards.

## 7. Pass bar for MVP demo

- Evidence support ≥95% on auto-validated output
- Published-set precision ≥90% after human review on gold

## 8. Public site evaluation (Observatory) — important

**Public site evaluation is corpus description, not prevalence.**

Analytics charts, decision counts, year histograms, and sanction/issue tables on
Observatory describe **only the decisions included in that publication release**.
They must not be interpreted as:

- rates across all MCHK/DCHK judgments;
- population risk or “typical” sanction practice;
- statistically representative samples unless a future release explicitly
  documents sampling design and coverage.

Synthetic_demo releases are engineering corpora. Real public releases (when
policy allows) must still state inclusion/exclusion criteria and source cutoff
dates in the release manifest (`inclusion_criteria`, `exclusion_criteria`,
`source_cutoff_date`, `global_caveats`).

## Milestone 1 automated gates (current)

Already enforced in unit tests:

- Schema validation errors = 0 on mock outputs for synthetic fixtures
- Evidence support rate = 100% after quote alignment
- Every published proposition resolves to a page span id

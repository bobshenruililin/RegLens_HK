# Phase 0 approval record

| Field | Value |
|-------|-------|
| Package | RegLens HK — Phase 0 Planning Package |
| Status | **Approved** |
| Approved by | Product stakeholder (implementation request) |
| Approved at | 2026-07-11 |
| Locked regulators | MCHK, DCHK (NCHK deferred) |
| Locked access posture | Internal research / organisational non-commercial use until written commercial consent |
| Scope cuts accepted | See `docs/MILESTONES.md` § exclusions and further reductions |

## Decisions locked on approval

1. MVP bodies: Medical Council of Hong Kong + Dental Council of Hong Kong only.
2. No live scraping or source adapters in MVP.
3. Semantic search ships behind a feature flag; FTS is the primary path.
4. OCR is fallback-only for insufficient text layers.
5. `legal_test` propositions are always `epistemic_class=interpretation` and review-mandatory.
6. Public commercial republication of judgment text is blocked until consent is granted.

## Open questions (defaults applied)

| Question | Default until overruled |
|----------|-------------------------|
| Commercial intent for six-week deliverable | Internal-only |
| Human reviewers | Engineers + designated legal reviewer |
| LLM vendor | Stub in CI; production TBD after DPA |
| Hosting | Docker Compose local (+ optional shared staging later) |
| Gold set owners | Project team; double annotation |
| Appeal status | Judgment-stated only |
| NCHK | Deferred to Phase 1 |

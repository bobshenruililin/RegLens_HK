# Phase 0 approval record

| Field | Value |
|-------|-------|
| Package | RegLens HK — Phase 0 Planning Package |
| Status | **Approved** |
| Approved by | Product stakeholder (implementation request to commit Phase 0 package) |
| Approved at | 2026-07-11 |
| Locked regulators | **MCHK**, **DCHK** (NCHK deferred to Phase 1) |
| Locked access posture | Internal research / organisational **non-commercial** use until written commercial consent |
| Schema / extraction | Approved as specified in Phase 0 package |
| Architecture | Next.js + Python worker + PostgreSQL/pgvector + object storage + one worker |

## Decisions locked on approval

1. MVP bodies: Medical Council of Hong Kong + Dental Council of Hong Kong only.
2. No live scraping or source adapters until source terms are reviewed and separately approved.
3. Semantic search may ship behind a feature flag; keyword FTS is the primary path.
4. OCR is fallback-only when the text layer is insufficient.
5. `legal_test` propositions are always `epistemic_class=interpretation` and review-mandatory.
6. Public commercial republication of judgment text is blocked until consent is granted.
7. Appeal status in MVP is **as stated in the judgment only** (no separate Court of Appeal corpus).

## Open questions — defaults applied

| Question | Default until overruled |
|----------|-------------------------|
| Commercial intent for six-week deliverable | Internal-only |
| Human reviewers | Engineers + designated legal reviewer |
| LLM vendor | Stub/mock in CI and Milestone 1; production TBD after DPA |
| Hosting | Docker Compose local (+ optional shared staging later) |
| Gold set owners | Project team; double annotation with adjudicator |
| Appeal status | Judgment-stated only |
| NCHK | Deferred to Phase 1 |

## Implementation gate

- Phase 0 docs and schemas: this branch / PR.
- Licence posture: internal-use confirmed; commercial consent letters drafted (not yet sent by authorised human).
- Week 1 foundations: already landed on `main` via PR #1 (Compose, migrations, fixture ingest, mock LLM, decision page). Further weeks require separate milestone approval.

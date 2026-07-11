# Assumptions and open questions

## Assumptions (proceed unless overruled)

| ID | Assumption |
|----|------------|
| A1 | MVP covers **MCHK + DCHK only**. NCHK is Phase 1 because its corpus is thinner, more heterogeneous (website PDFs since ~2016 + Gazette orders), and would force a third parser before provenance is proven. |
| A2 | Corpus is **manually downloaded fixtures** under `fixtures/raw/{regulator}/` with a manifest. No crawlers, authenticated sessions, or CAPTCHA bypass. |
| A3 | Initial product surface is **internal tooling** (auth-gated), not a public commercial SaaS. MCHK copyright notice permits free reproduction of text for personal/internal organisational use, **not** commercial purposes; commercial use needs prior written consent (`mchk@dh.gov.hk`). |
| A4 | Practitioner names in published judgments are intentionally public and may be indexed; **patient / complainant / third-party personal data** must be suppressed or left only inside raw spans behind review controls. |
| A5 | One LLM provider behind an interface; default local/dev provider is a mock/stub returning schema-validated JSON. Production provider chosen only after DPA review. |
| A6 | **Page-level spans** are the provenance unit for MVP; paragraph/char offsets are stored when available but UI highlights at page (and optional quote) granularity. |
| A7 | PostgreSQL hosts relational data, `tsvector` FTS, and `pgvector` embeddings. Object storage (S3-compatible, MinIO locally) holds immutable originals. |
| A8 | English is primary. Chinese text is preserved in raw/OCR layers; bilingual extraction is out of MVP. |
| A9 | Human review is required before any extraction set is `published`. Draft/auto-extracted data is visible only to reviewers (synthetic demo seeds may be pre-accepted for local UX only). |
| A10 | Target fixture set: ~40–80 decisions (roughly 20–40 per regulator), curated for format diversity, not completeness. |

## Open questions

1. **Commercial intent:** Is the six-week deliverable internal-only, or must it be publicly reachable? *(Default: internal-only.)*
2. **Who are the human reviewers?** Legal ops, clinical advisors, or engineers?
3. **LLM vendor constraint:** Allowed providers, data-residency, and whether document text may leave the VPC.
4. **Hosting:** Local Docker only for MVP demo, or also a shared staging environment?
5. **Gold set size and owners:** Who labels the evaluation set, and what inter-annotator process?
6. **Appeal status:** Judgment-stated only, or also later Court of Appeal outcomes as separate sources? *(Default: judgment-stated only.)*
7. **NCHK timeline:** Confirm deferral, or force three regulators into MVP? *(Default: defer.)*

See also [`approvals/PHASE0_APPROVAL.md`](approvals/PHASE0_APPROVAL.md).

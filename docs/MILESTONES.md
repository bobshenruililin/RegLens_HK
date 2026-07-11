# Six-week milestone plan

| Week | Outcome | Exit criteria |
|------|---------|---------------|
| **W1 — Foundations & licence gate** | Repo, Compose (Postgres+pgvector, MinIO, web, worker), migrations, audit template filled for MCHK+DCHK, fixture SOP, fixtures hashed | Licence rows completed; ingest writes immutable blob + DB/local record idempotently |
| **W2 — Parse & spans** | PDF/HTML text pipeline, OCR fallback, page spans, coverage metrics | ≥90% pages have usable text on gold PDFs; span IDs stable across re-runs |
| **W3 — Extraction v1** | Deterministic parsers for headers/case refs/sanctions where possible; LLM fill for remainder; strict schema + quote check | Invalid JSON rejected 100%; no proposition without evidence array |
| **W4 — Review & publish** | Review queue UI, edit/reject, publish gate, audit log, coverage warnings | Cannot publish without spans + human accept/edit |
| **W5 — Search & decision UX** | FTS filters, decision page with highlight jump, thin semantic search over published propositions/spans | Keyword search usable; semantic optional behind flag if quality weak |
| **W6 — Eval, harden, demo** | Gold-set scoring, job resume tests, privacy redaction pass, demo script, exclusions list signed off | Eval report + risk register updated; demo on fixtures only |

## Status

| Week | Status |
|------|--------|
| W1 | **Done** on `main` (PR #1) — Compose files, migrations, fixture ingest, hashing, page segmentation, mock LLM, decision page, tests |
| W2–W6 | Not started; require separate milestone approval |

## Further scope reductions

See [`EXCLUSIONS.md`](EXCLUSIONS.md) § further reductions.

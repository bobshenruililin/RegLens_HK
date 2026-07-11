# MVP Backbone (2A–2D)

Implementation notes for the approved backbone under continuing restrictions
(internal/non-commercial; no crawl; no public real-document republication;
mock LLM only; no NCHK; FTS before semantic).

## 2A — Contracts, determinism, privacy, CI

- Shared enums/types: `packages/contracts/`
- Deterministic document/decision/span IDs and job `dedupe_key`
- Derived-field PII redaction (`Patient`, `Madam xxx`, etc.)
- GitHub Actions: pytest + schema checks + Next.js typecheck/build

## 2B — PostgreSQL, object storage, jobs

- Object store protocol: local filesystem (default) + optional S3/MinIO
- Postgres repository layer (optional when `DATABASE_URL` set)
- Job enqueue / claim / complete with unique `dedupe_key`
- CLI: `python -m reglens_worker jobs …`

## 2C — Review, publication, authentication

- Cookie session auth (`AUTH_PASSWORD` / `REGLENS_SESSION_SECRET`)
- Review queue UI + API
- Publish gate: spans required + `accepted`/`edited` only
- Ingest default: propositions land as `pending` (not published)

## 2D — FTS + evidence UX

- Keyword FTS over published claims + page text (Postgres `tsvector` when DB available; local fallback indexer otherwise)
- Filters: regulator, profession, prop_type
- Decision page highlights evidence quotes in source pages

Semantic / pgvector search remains disabled.

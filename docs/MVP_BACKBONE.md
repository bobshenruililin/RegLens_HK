# MVP Backbone vs MVP-RC1

## Experimental backbone (2A–2D)

Implementation notes for the approved backbone under continuing restrictions
(internal/non-commercial; no crawl; no public real-document republication;
mock LLM only; no NCHK; FTS before semantic).

### 2A — Contracts, determinism, privacy, CI (complete)

- Shared enums/types: `packages/contracts/`
- Deterministic document/decision/span IDs and job `dedupe_key`
- Derived-field PII redaction (`Patient`, `Madam xxx`, etc.)
- GitHub Actions: pytest + schema checks + frontend typecheck/build

### 2B — PostgreSQL, object storage, jobs (**experimental**)

- Object store protocol: local filesystem (default) + optional S3/MinIO
- Postgres repository layer (optional when `DATABASE_URL` set)
- Job enqueue / claim / complete with unique `dedupe_key`
- CLI: `python -m reglens_worker jobs …`

**Status:** scaffolding present; not production-ready; not required for Observatory.

### 2C — Review, publication, authentication (**experimental**)

- Cookie session auth (`AUTH_PASSWORD` / `REGLENS_SESSION_SECRET`) in Studio
- Review queue UI + API in `apps/studio`
- Publish gate: spans required + `accepted`/`edited` only
- Ingest default: propositions land as `pending` (not published)

**Status:** local Studio only; fail-closed production auth; never Pages-hosted.

### 2D — FTS + evidence UX (**experimental**)

- Keyword FTS over published claims + page text (Postgres `tsvector` when DB
  available; local fallback indexer otherwise)
- Filters: regulator, profession, prop_type
- Decision page highlights evidence quotes in source pages

Semantic / pgvector search remains disabled. Studio search may still be
substring matching over local seed files.

## MVP-RC1 (current delivery) vs experimental 2B–2D

| Concern | Experimental 2B–2D | MVP-RC1 |
|---------|--------------------|---------|
| Public product | Not defined | RegLens Observatory (`apps/site`) |
| Internal UI path | Was `apps/web` | Renamed / split: `apps/studio` |
| Publication | Review “publish” into seed | Versioned `release build` + policy + privacy scan |
| Hosting | Auth web app (not static-exportable) | Static export → GitHub Pages |
| Search for public users | N/A | Client-side catalog filter |
| Real corpus on public web | Forbidden | Still forbidden (`internal_only`) |

**Do not treat 2B–2D modules as RC1 acceptance criteria.** RC1 acceptance is the
Studio/Observatory separation, synthetic_demo release pipeline, public-scan
guards, and static Observatory — built on the completed 2A trust foundation.

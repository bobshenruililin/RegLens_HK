# Six-week / backbone milestones

| Item | Status |
|------|--------|
| W1 Foundations | Done |
| Phase 0 docs | Done |
| **Milestone 2A — Trusted contracts, deterministic artifacts, CI** | **Complete** |
| Milestone 2B — PostgreSQL, object storage, jobs | Experimental / partial (not production-ready) |
| Milestone 2C — Review, publication, authentication | Experimental / partial (Studio only; not production-ready) |
| Milestone 2D — Keyword search and evidence UX | Experimental / partial (substring/local; not production FTS) |
| **MVP-RC1 — RegLens Observatory** | **This delivery** |

## Milestone 2A (complete)

- Default extraction pending/unpublished
- Synthetic vs private-data separation
- Extraction contract v2 + domain validation
- Immutable run identity with output SHA-256
- Parser safety limits and page-quality reporting
- `make verify` / CI green

## Experimental 2B–2D code

Worker modules (`jobs`, `db`, `objectstore`, `publication`, `search`) and Studio
auth/review/search UI exist as **local experimental** scaffolding. They are not
represented as production-ready. Object store is unwired; Studio search is
keyword/substring over local seed files; Postgres FTS requires `DATABASE_URL`
and is not used by the public site.

## MVP-RC1 — RegLens Observatory

Public, read-only, static research website (GitHub Pages) consuming a versioned
privacy-checked publication release. Trust boundaries:

- **RegLens Studio** (`apps/studio`) — internal; never deployed to Pages
- **RegLens Observatory** (`apps/site`) — public static export only

Semantic search, OCR, live crawl, NCHK, real LLM, and real public republication
remain blocked.

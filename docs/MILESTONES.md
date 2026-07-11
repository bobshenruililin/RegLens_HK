# Six-week / backbone milestones

| Item | Status |
|------|--------|
| W1 Foundations | Done |
| Phase 0 docs | Done |
| **Milestone 2A — Trusted contracts, deterministic artifacts, CI** | **Complete** |
| Milestone 2B–2D experimental scaffolding | Superseded by RC2 data plane (archived migrations) |
| **MVP-RC1 — RegLens Observatory** | **Complete** |
| **MVP-RC2 — Studio trusted data plane** | **This delivery** |

## Milestone 2A (complete)

- Default extraction pending/unpublished
- Synthetic vs private-data separation
- Extraction contract v2 + domain validation
- Immutable run identity with output SHA-256
- Parser safety limits and page-quality reporting
- `make verify` / CI green

## MVP-RC1 — RegLens Observatory (complete)

Public, read-only, static research website (GitHub Pages) consuming a versioned
privacy-checked publication release. Trust boundaries:

- **RegLens Studio** (`apps/studio`) — internal; never deployed to Pages
- **RegLens Observatory** (`apps/site`) — public static export only

## MVP-RC2 — Trusted data plane (this delivery)

PostgreSQL operational SoT when `REGLENS_MODE=postgres`; demo filesystem mode
retained for `make verify`. Checkpoint D (partial) adds:

- Makefile: `integration`, `db-*`, `demo-enqueue`, `worker-once`,
  `postgres-demo-pipeline` / `postgres-demo-release`,
  `site-build-from-postgres-release`, `rc2-acceptance`
- Compose on `postgres:16` (no pgvector); migrate-required docs
- CI job `postgres-integration`
- Operator docs + ADRs 0008–0012
- Synthetic-only `scripts/postgres_demo_pipeline.py`

Continuing restrictions: no crawl, OCR, real LLM, semantic search, NCHK,
Studio-on-Pages, or breaking `publication_release.v1`.

`make verify` remains the **RC2 demo-mode gate** (no `DATABASE_URL` required).
Postgres path is gated by `make integration` / CI `postgres-integration`.

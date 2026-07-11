# Six-week / backbone milestones

| Item | Status |
|------|--------|
| W1 Foundations | Done |
| Phase 0 docs | Done |
| **Milestone 2A — Trusted contracts, deterministic artifacts, CI** | **Complete** |
| Milestone 2B–2D experimental scaffolding | Superseded by RC2 data plane (archived migrations) |
| **MVP-RC1 — RegLens Observatory** | **Complete** |
| **MVP-RC2 — Studio trusted data plane** | **Complete** |
| **MVP-RC3 — Live source sync and real corpus pilot** | **Complete** |
| **MVP-RC4 — Core10 research and public Observatory enrichment** | **This delivery** |

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

At RC2 close, continuing restrictions were: no crawl, OCR, real LLM, semantic
search, NCHK, Studio-on-Pages, or breaking `publication_release.v1`.

`make verify` remains the **RC2 demo-mode gate** (no `DATABASE_URL` required).
Postgres path is gated by `make integration` / CI `postgres-integration`.

## MVP-RC3 — Source sync and internal pilot (complete)

RC3 adds policy-aware source metadata sync, MCHK/DCHK adapters, local OCR text
variants, bounded extractor/critic tests, and the Core 50 internal pilot plan.
Focused checks: `make rc3-verify`, `make sources-status`,
`make source-sync-mchk-dry`, `make source-sync-dchk-dry`, `make core50-status`.

Continuing restrictions: public availability is not reuse permission; robots.txt
is not a licence; MCHK remains internal-only; DCHK carries the July 14, 2018
caveat; no public real release; no complete de-identification claim; and
student-research letters do not unlock Pages.

## MVP-RC4 — Core10 research and public Observatory enrichment (this delivery)

RC4 adds an editorial codebook, Core10 operations before Core50 scale, five-user
research protocol, product positioning, and research-collection definitions. The
public Observatory gains synthetic-only tour, questions, and roadmap pages.

Focused checks: `make core10-report`, `make rc4-verify`, and
`pytest tests/test_rc4_public_pages.py`.

Continuing restrictions: GitHub Pages is publicly accessible; real Core10/Core50
corpus material, OCR text, reviewer notes, and internal research outputs stay in
Studio/private storage until legal approval and source policy permit a public
real release.

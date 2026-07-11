# MVP-RC1 baseline

Recorded before MVP-RC1 implementation on branch
`cursor/reglens-hk-mvp-rc1-3150` (from Milestone 2A reapply tip).

Date: 2026-07-11

## Commands

| Command | Result |
|---------|--------|
| `make verify` | PASS (exit 0) |
| Fixture safety (`scripts/check_fixtures.py`) | PASS |
| `ruff check` / `ruff format --check` | PASS |
| `mypy` | PASS |
| `pytest` | 24 passed |
| `apps/web` `npm ci` + typecheck + build | PASS (Next.js 14.2.35) |

## Pre-existing defects (not treated as regressions)

1. Privacy redaction not applied on ingest; “Patient A” retained in derived claims.
2. Domain validation requires `span_id` presence but does not verify stable-ID equality.
3. Tracked `fixtures/seed/` contains duplicate m1 + m2a decision generations.
4. Vacuous `or True` assertions in `tests/test_m1_pipeline.py`.
5. Mock truncation / hearing-as-judgment / appeal-in-sanction defects.
6. Web search labeled FTS but implements substring matching.
7. Web review can write into tracked `fixtures/seed/`.
8. Docs mark 2B–2D “not started” while partial backbone code exists.
9. Authenticated `apps/web` cannot be statically exported for GitHub Pages.

## Milestone status (reconciled)

| Item | Status |
|------|--------|
| Milestone 2A | Complete (trusted contracts, immutable runs, CI) |
| Milestone 2B–2D | Experimental/partial code present; **not** production-ready |
| MVP-RC1 Observatory | This delivery (public static site + publication release) |

## Implementation plan (concise)

1. Repair trust foundation: fixtures layout, privacy, provenance, mock quality, confidence boundary.
2. Add publication release schemas, taxonomy, annotations, and `release build` CLI.
3. Rename `apps/web` → `apps/studio` (internal only); add `apps/site` static Observatory.
4. Ship Pages workflow that builds synthetic release into static export only.
5. Expand tests/CI/Makefile/docs and ADRs 0004–0006.

Docker CLI was previously unavailable in this environment; will re-check during acceptance.

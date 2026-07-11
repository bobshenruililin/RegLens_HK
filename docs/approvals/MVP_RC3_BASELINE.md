# MVP-RC3 baseline (pre-implementation)

| Field | Value |
|-------|-------|
| Branch | `cursor/mvp-rc3-live-corpus` |
| Tip at baseline | `fe8b8ad` (consent postal-approval record) |
| RC2 merge on main | `ddf8b13` |
| Timestamp (UTC) | 2026-07-11T14:50:00Z |
| Docker CLI | **Unavailable** (`docker` not found) |
| Local Postgres | Available (`127.0.0.1:5432`, local-only credentials) |

## Command results

| Command | Result |
|---------|--------|
| `git status` | Clean on `cursor/mvp-rc3-live-corpus` before RC3 code edits |
| `make verify` (no `DATABASE_URL`) | **PASS** |
| `make db-migrate` / `db-status` | **PASS** (`0001`, `0002` applied) |
| `make integration` | **PASS** (marker + pg/jobs/equivalence) |
| `make rc2-acceptance` | **PASS** (verify + integration + postgres-demo-pipeline + scan) |
| Studio / Site production builds | **PASS** (via verify) |
| Docker Compose | **Not run** (Docker unavailable) |

## Focused RC2 trust audit (pre-network)

| Area | Finding | Action |
|------|---------|--------|
| Publication transaction | Approve path validates accepted/edited + evidence + annotations; synthetic_demo refuses real | Retain; RC3 must not bypass |
| Role enforcement | Studio roles reviewer/publisher/admin; worker cannot publish | Retain |
| Immutable revisions | Append-only revisions; extracted props ON CONFLICT DO NOTHING | Retain |
| Job leases | SKIP LOCKED + backoff + dead-letter | Retain |
| Object-store hash verify | Typed errors; CAS local store | Retain |
| Postgres fail-closed | `REGLENS_MODE=postgres` requires `DATABASE_URL` | Retain |
| Public release policy | MCHK/DCHK `internal_only` in `source_publication_policy.v1.json` | **Do not change in RC3** |

## Critical/high defects before sync

None blocking identified in the above audit. Proceed to RC3 source-sync implementation with fail-closed policy gates.

## Notes

- Ordinary CI must not hit live regulator sites.
- Real PDFs must never enter Git/CI/Pages.
- Owner-reported student-research postal letters do **not** unlock public real releases.

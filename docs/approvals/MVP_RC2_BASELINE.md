# MVP-RC2 baseline

Recorded on branch `cursor/mvp-rc2-trusted-data-plane` at tip matching
`main` @ `b88882d` (RC1 + Pages base-path fix), before RC2 edits.

Date (UTC): 2026-07-11

## Commands

| Command | Result |
|---------|--------|
| `git status` | Clean on `cursor/mvp-rc2-trusted-data-plane` |
| `make verify` | PASS (exit 0) |
| Fixture safety | PASS |
| `ruff check` / `ruff format --check` | PASS |
| `mypy` | PASS |
| `pytest` | **56 passed** |
| Studio npm ci / typecheck / build | PASS |
| Site npm ci / typecheck / static build | PASS |
| demo release + public scan | PASS |
| Docker | **Unavailable** (`docker: command not found`) |

## Pre-existing experimental 2B–2D code

| Area | Path | RC2 disposition |
|------|------|-----------------|
| Experimental migrations | `packages/db/migrations/001_init.sql`, `002_proposition_fts.sql` | **Replace** with clean `0001_rc2_baseline.sql` (reset approved) |
| Optional PG persist | `services/worker/reglens_worker/db.py` | **Replace** with repositories |
| Job queue (file/PG) | `jobs.py` | **Replace** with lease/retry model |
| Object store (unwired) | `objectstore.py` | **Replace** / wire as sole blob path |
| File seed store | `store.py` | **Retain** for `REGLENS_MODE=demo` |
| Studio FS review | `apps/studio/lib/data.ts` | **Replace** data plane in postgres mode |
| HMAC password auth | `apps/studio/lib/auth.ts` | **Replace** with hashed users/sessions |
| Release builder | `release.py` | **Retain** contract; **add** postgres input adapter |
| Observatory | `apps/site` | **Retain unchanged** |
| `publication_release.v1` | `publications/schemas/*` | **Frozen** — no breaking changes |

## Environment checks for schema reset

- `DATABASE_URL`: unset
- `.env`: absent
- Non-local DB: not detected
- Real persistent corpus: none

**Conclusion:** pre-production clean baseline reset proceeds under
`docs/approvals/MVP_RC2_APPROVAL.md`.

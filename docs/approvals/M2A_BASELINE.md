# Milestone 2A baseline (pre-change)

Recorded before editing for Milestone 2A.

## Commands and results

### Python tests
```
export PYTHONPATH=services/worker
pytest
```
Result: **10 passed** in 0.15s. Exit 0.

### npm ci
```
cd apps/web && npm ci
```
Result: **Exit 0** (29 packages). npm audit reported 2 vulnerabilities (pre-existing upstream advisories).

### Next.js production build
```
cd apps/web && npm run build
```
Result: **Exit 0**. Compiled successfully; routes `/`, `/decisions/[id]`.

### docker compose config
```
docker compose config
```
Result: **Pre-existing environment failure** — `docker: command not found` in this agent environment. Compose file itself was not modified before baseline. Will re-validate file syntax after pinning image tags; Docker daemon may still be unavailable.

## Distinction

- Pre-existing: Docker CLI absent in this environment.
- New work must not introduce Python/web regressions relative to this baseline.

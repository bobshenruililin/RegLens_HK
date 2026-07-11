# Relational schema

Canonical SQL (prepared for later milestones): [`packages/db/migrations/001_init.sql`](../packages/db/migrations/001_init.sql).

## Milestone 2A local artifacts

```text
data/
  objects/sha256/ab/<sha>          # immutable raw bytes
  meta/documents/<sha>.json
  meta/spans/<sha>.json
  meta/runs/<run_key>/
    extraction.json                # immutable
    extraction.sha256
    decision.json                  # immutable pending decision view
    quarantine/                    # conflicting outputs if any
  seed/decision.json               # mutable synthetic demo pointer only
```

Persistent IDs are derived from `run_key` + `client_ref` (see ADR 0002).
PostgreSQL wiring is Milestone 2B.

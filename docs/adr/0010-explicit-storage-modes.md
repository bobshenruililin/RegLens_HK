# ADR 0010 — Explicit storage modes

## Status

Accepted (MVP-RC2)

## Context

Experimental 2B code sometimes “optionally” wrote to Postgres when
`DATABASE_URL` was set, blurring demo filesystem demos and operational DBs.
Operators could not tell which SoT was active.

## Decision

Introduce explicit `REGLENS_MODE`:

| Mode | SoT | DSN |
|------|-----|-----|
| `demo` (default) | Filesystem under `DATA_ROOT` | Not required |
| `postgres` | PostgreSQL + object store | **Required** (fail closed) |

Job queue, ingest enqueue, and Studio data access switch on mode — not on
“DSN present ⇒ maybe Postgres”.

`make verify` remains the **demo-mode gate**. Postgres integration is a separate
CI job / `make integration`.

## Consequences

- Misconfiguration fails loudly instead of half-writing two stores.
- Legacy optional `db.persist_ingest_to_postgres` is not the RC2 control plane.
- Docs and Makefile must state which targets need `DATABASE_URL`.

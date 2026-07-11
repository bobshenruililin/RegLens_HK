# ADR 0011 — Publication transaction

## Status

Accepted (MVP-RC2)

## Context

Shipping “whatever Studio can see” to Observatory would leak pending claims,
raw text, and internal-only sources. RC1 froze `publication_release.v1`; RC2
must feed that contract from Postgres without weakening checks.

## Decision

Publication is an explicit transaction:

1. Draft `publication_releases` + items
2. Fail-closed `validate_release` (fixture_kind vs mode, evidence, annotations,
   no mixed corpus, `internal_only` blocked for `public`)
3. Optimistic `approve_and_build_release` → status `ready`
4. Compile bundle with `build_release_from_postgres` (same privacy/schema path
   as filesystem `release build`)
5. Public-scan before Pages/site copy

`publication_release.v1` schemas stay **frozen** (no breaking changes).

## Consequences

- Observatory never queries live Postgres.
- Demo pipeline may auto-accept synthetic rows only, still through this gate.
- Version conflicts on approve fail closed.

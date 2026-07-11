# ADR 0008 — Stable decision identity

## Status

Accepted (MVP-RC2)

## Context

Studio and publication need a stable primary key for a decision across re-ingest,
review edits, and release rebuilds. Filesystem demos used string ids derived from
fixtures; Postgres requires UUID keys without breaking Observatory slugs.

## Decision

- Decision UUID = `uuid5(URL_NAMESPACE, "reglens:decision:{source_id}:{external_ref}")`
  via `pg.decisions.decision_id_for`.
- Uniqueness enforced on `(source_collection_id, external_ref)`.
- Public Observatory slug derives from `external_ref` (`public_slug_from_external_ref`),
  not from the UUID.
- Re-ingest upserts the same decision id; extraction runs remain append-only.

## Consequences

- IDs are deterministic across demo and postgres modes for the same source/ref.
- Changing `external_ref` creates a new decision identity — treat refs as durable.
- Slug validation rejects unsafe characters for static paths.

# ADR 0001 — Extraction contract v2

## Status

Accepted (Milestone 2A)

## Context

Milestone 1 used `extraction_result.v1.json` with provider-generated UUIDs and a single `case_ref` / `decision_date`. That conflated model output identity with database identity and limited temporal modelling.

## Decision

Introduce `extraction_result.v2.json` (`schema_version: 2.0.0`) where:

- providers emit `client_ref` only (no persistent UUIDs);
- `decision_metadata` and `coverage` are required;
- multiple `case_refs` and typed `dates` are supported;
- propositions carry `derivation` and optional `relations` by `client_ref`;
- evidence requires `page_no` + `quote`; `span_id` is required after application span resolution;
- character offsets are paired and validated.

v1 remains loadable for migration via `migrate_v1_to_v2`.

## Consequences

Application code assigns deterministic UUIDs from run key + `client_ref`. Domain validators enforce regulator allow-lists, quote/span integrity, and relation endpoints.

# ADR 0009 — Immutable proposition revisions

## Status

Accepted (MVP-RC2)

## Context

Mutable “edit in place” proposition rows made audit trails unreliable and
allowed silent overwrite of model output. RC2 needs human edits without losing
extractor provenance.

## Decision

- `extracted_propositions` are immutable extractor outputs (client_ref scoped).
- Edits append `proposition_revisions` with monotonic `revision_number`.
- Reviews attach to a specific revision; pending is the default ingest state.
- Optimistic concurrency: writers supply `expected_head_revision_number`;
  mismatch → `RevisionConflictError` (fail closed).
- Publishable heads are `accepted` or `edited` with ≥1 evidence link.

## Consequences

- No silent mutation of model claims.
- Review UI and APIs must reload heads after conflict.
- Demo auto-accept creates labelled review rows; it does not rewrite revision 1
  text unless an edit path is used.

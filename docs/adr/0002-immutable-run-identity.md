# ADR 0002 — Immutable run identity

## Status

Accepted (Milestone 2A)

## Context

Overwriting extraction JSON under a document hash hid non-determinism and destroyed audit history.

## Decision

Compute `run_key = SHA-256(document_hash | schema | pipeline | provider | model | prompt | settings)`.

Store extraction and decision artifacts under `meta/runs/{run_key}/` with an `extraction.sha256` sidecar. Writes are atomic. Re-running the same key with identical bytes is a no-op; differing bytes quarantine the new payload and raise `DeterministicRunConflict`.

A mutable `data/seed/decision.json` pointer may exist for synthetic demos but is not the audit record.

## Consequences

Persistent proposition IDs are `uuid5(run_key, client_ref)`. Reproducibility is testable. Conflicts surface immediately.

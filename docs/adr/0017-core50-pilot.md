# ADR 0017 — Core 50 pilot

## Status

Accepted (MVP-RC3)

## Context

The project needs a small real-corpus pilot to test review and extraction
coverage beyond synthetic fixtures while preserving licensing and privacy limits.

## Decision

Define Core 50 as an internal research pilot, not a public dataset:

- 25 planned MCHK records and 25 planned DCHK records;
- selection guided by `publications/pilot/core50.v1.json`;
- no real PDFs, OCR text, page text, or derived public release artifacts in Git;
- human review required; auto-accept remains synthetic-demo only.

Public availability is not reuse permission, and robots.txt is not a licence.
MCHK remains internal-only. DCHK records must preserve the July 14, 2018 caveat.
Student-research letters support internal research posture but do not unlock
Pages publication.

## Consequences

- Core 50 can measure operational readiness without prevalence claims.
- RC3 makes no public real release and no complete de-identification claim.
- Any future public real release requires separate source-policy approval.

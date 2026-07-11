# ADR 0014 — Source versioning

## Status

Accepted (MVP-RC3)

## Context

Official source indexes change over time. RC3 needs to know what was seen,
parsed, and reviewed without committing real documents or treating index
presence as publication permission.

## Decision

Persist source-sync runs, index snapshots, discovered source items, URL aliases,
hashes, parser health, and caveats in the trusted data plane. Stable source item
keys are adapter-owned; application IDs remain separate.

Versioning records provenance for internal review only. It does not alter
`source_publication_policy`: MCHK and DCHK remain `internal_only` for public
release. DCHK records retain the July 14, 2018 caveat. robots.txt observations
may be recorded, but robots is not a licence.

## Consequences

- Operators can compare source drift and parser regressions.
- Student-research letters remain evidence for internal research posture, not
  Pages publication.
- No RC3 public real release or complete de-identification claim follows from
  source versioning.

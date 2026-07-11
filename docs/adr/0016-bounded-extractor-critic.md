# ADR 0016 — Bounded extractor/critic

## Status

Accepted (MVP-RC3)

## Context

RC3 needs better extraction checks without allowing model output to become
authoritative or public by default. Real text may carry privacy and licensing
constraints.

## Decision

Use a bounded extractor/critic flow:

1. deterministic parsing and evidence spans first;
2. extractor output constrained by schema and ontology;
3. critic pass for contradictions, missing evidence, and uncertainty;
4. reconciliation into pending/unpublished propositions;
5. human review before acceptance.

Network LLM use on real text requires explicit runtime approval. Public
availability does not permit provider processing or republication; robots.txt is
not a licence. MCHK remains internal-only, DCHK outputs preserve the July 14,
2018 caveat, and student-research letters do not unlock Pages.

## Consequences

- Model output cannot bypass review or source policy.
- RC3 creates no public real release.
- Privacy scans and bounded prompts do not justify complete de-identification
  claims.

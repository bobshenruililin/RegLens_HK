# ADR 0020 - Editorial codebook

## Status

Accepted (MVP-RC4)

## Context

RegLens needs consistent human review across charge, finding, sanction, factor,
authority, takeaway, and uncertainty fields. Without a codebook, reviewers may
mix factual extraction, interpretation, and product copy.

## Decision

Adopt `docs/EDITORIAL_HANDBOOK.md` as the RC4 editorial codebook.

The handbook:

- uses synthetic examples only;
- preserves `epistemic_class` and `derivation`;
- separates decision metadata from coded propositions;
- treats takeaways as human-authored interpretation;
- requires uncertainty to be recorded rather than guessed away.

## Consequences

- Core10/Core50 reviewers share a common vocabulary.
- Public synthetic pages can explain the same concepts without exposing real
  examples.
- Future schema or taxonomy changes should update the handbook and cite this
  ADR.

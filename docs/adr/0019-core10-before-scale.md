# ADR 0019 - Core10 before Core50 scale

## Status

Accepted (MVP-RC4)

## Context

ADR 0017 defined an internal Core50 pilot. Before scaling to 50 real decisions,
the team needs a smaller operational checkpoint to validate metadata sync,
acquisition, extraction, review, uncertainty handling, and reporting.

## Decision

Introduce Core10 as an internal readiness loop before Core50.

Core10 follows this sequence:

1. metadata sync;
2. acquire;
3. extract;
4. review;
5. internal research.

The public repository may contain synthetic/demo report tooling and synthetic
outputs. It must not contain real Core10 PDFs, HTML, OCR text, full page text, or
Pages release artifacts.

## Consequences

- Operators can validate the workflow before Core50.
- Human interpretation gaps are visible early.
- Core10 results are not a statistical sample and must not be presented as
  prevalence.
- Public real publication remains blocked until a separate approval changes the
  source-policy posture.

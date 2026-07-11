# ADR 0005 — Publication release boundary

## Status

Accepted (MVP-RC1)

## Context

Internal stores retain immutable raw documents, full page text, model
confidence, and pending propositions. Licensing for MCHK/DCHK does not allow
casual public republication. Shipping “whatever is in seed/” to Pages would
violate copyright posture and privacy minimisation.

## Decision

Introduce an explicit **publication release** step:

- CLI: `python -m reglens_worker release build`
- Inputs: reviewed decisions, editorial annotations, `source_publication_policy`,
  taxonomy
- Outputs: versioned bundle under `generated/public-release` conforming to
  `publications/schemas/*`
- Gate: `scripts/check_public_release.py` (checksums + privacy scan)

`release_mode` is either `synthetic_demo` or `public`:

- `synthetic_demo` accepts only `fixture_kind=synthetic` and labels outputs as demo.
- `public` accepts only real decisions and **refuses** sources with
  `visibility: internal_only`.

Current policy files keep MCHK/DCHK at `internal_only`, so real public releases
are blocked until licensing posture changes. Consent statuses in the human
audit are not rewritten by this mechanism.

Observatory and Pages may consume **only** this bundle (via `make pages-artifact`).

## Consequences

- No raw documents on GitHub Pages.
- Policy becomes executable, testable, and CI-enforced.
- Operators cannot “just copy data/” into the site public folder without failing
  scans and review.
- Analytics counts are explicitly scoped to the release corpus.

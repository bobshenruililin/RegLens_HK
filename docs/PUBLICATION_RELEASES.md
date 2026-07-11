# Publication releases

A **publication release** is the only approved package of RegLens data that may
leave the Studio/local artifact boundary into Observatory or GitHub Pages.

## Why a release boundary exists

Internal artifacts (`data/objects`, `data/meta`, review JSON) contain raw bytes,
full page text, model confidence, and pending propositions. Public consumers
must never see those. The release builder projects reviewed decisions into
privacy-minimised schemas, applies source policy, and fails closed on violations.

See ADR [`0005-publication-release-boundary.md`](adr/0005-publication-release-boundary.md).

## Inputs

| Input | Path (demo) |
|-------|-------------|
| Reviewed decisions | `data/seed/decisions/` (after ingest) |
| Editorial annotations | `publications/demo/editorial_annotations.v1.json` |
| Source policy | `publications/policies/source_publication_policy.v1.json` |
| Taxonomy | `publications/taxonomy/taxonomy.v1.json` |

CLI (also wrapped by `make demo-release`):

```bash
python -m reglens_worker release build \
  --data-root data \
  --annotations publications/demo/editorial_annotations.v1.json \
  --policy publications/policies/source_publication_policy.v1.json \
  --taxonomy publications/taxonomy/taxonomy.v1.json \
  --release-id demo-0.1.0 \
  --release-mode synthetic_demo \
  --released-at 2026-07-11T00:00:00Z \
  --output generated/public-release
```

Validate:

```bash
python scripts/check_public_release.py generated/public-release
# or: make public-scan
```

## Release modes

| `release_mode` | Fixture kinds | Policy |
|----------------|---------------|--------|
| `synthetic_demo` | `synthetic` only | Demo `public_excerpt`; real rows refused |
| `public` | `real` only | Per-source visibility; **`internal_only` refused** |

Current policy marks `mchk_judgments` and `dchk_judgments` as `internal_only`.
Therefore a real public release is **blocked by source policy** regardless of
Studio review state. Consent statuses in
[`SOURCE_LICENSING_AUDIT.md`](SOURCE_LICENSING_AUDIT.md) are not modified by the
builder.

## Outputs

```text
generated/public-release/
  release.json           # publication_release.v1 manifest
  catalog.json           # explore index
  analytics.json         # corpus aggregates for this release only
  checksums.sha256
  decisions/<slug>.json  # public_decision.v1
  csv/…                  # optional tabular exports
```

`make pages-artifact` copies this tree to `apps/site/public/data/release/`.

## What is stripped / forbidden

Public decisions must not include:

- model `confidence` or extractor/run metadata;
- full `pages[]` text arrays or raw PDF/HTML files;
- pending / rejected propositions;
- unretracted patient-style tokens that fail `scan_public_artifact`.

Evidence quotes are truncated to `max_excerpt_chars` (policy; demo default 280)
after derived-field redaction.

## Manifest semantics

`release.json` carries `decision_count`, `proposition_count`, inclusion/exclusion
criteria, methodology/taxonomy versions, and `global_caveats`. Those counts
describe **this published corpus**, not regulator-wide prevalence.

## Operator checklist

1. Ingest and review (Studio / seed decisions).
2. Ensure annotations cover every external_ref you intend to ship.
3. Confirm policy visibility matches licensing audit (do not casually flip).
4. `release build` with the correct `release_mode`.
5. `check_public_release.py` must pass.
6. Only then run `pages-artifact` / site build / Pages deploy.

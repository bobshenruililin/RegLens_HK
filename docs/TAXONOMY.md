# Public taxonomy (MVP-RC1)

Editorial classifications for Observatory are drawn from a versioned taxonomy
file, not from free-text model guesses at release time.

## Canonical file

[`publications/taxonomy/taxonomy.v1.json`](../publications/taxonomy/taxonomy.v1.json)

`taxonomy_version` is embedded into the publication release manifest and must
match the version referenced by editorial annotations
(`publications/schemas/editorial_annotations.v1.json`).

## Facets

| Facet | Field on public decision | Example codes |
|-------|--------------------------|---------------|
| Issue | `issue_categories` | `recordkeeping`, `consent`, `clinical_care`, `prescribing`, `advertising`, `dishonesty`, … |
| Finding outcome | `finding_outcomes` | `proved`, `partly_proved`, `not_proved`, `withdrawn`, `admitted`, `unknown` |
| Sanction | `sanction_categories` | `warning`, `reprimand`, `conditions`, `suspension`, `removal`, … |
| Factor | `factor_categories` | `clear_prior_record`, `admission`, `harm`, `remorse`, … |

Codes are stable identifiers; labels are for display. Release build rejects
annotations that reference unknown codes.

## Editorial annotations

Demo annotations:
[`publications/demo/editorial_annotations.v1.json`](../publications/demo/editorial_annotations.v1.json).

Each annotation is keyed by **`external_ref`** (stable case reference such as
`SYN-MCHK-2024-001`), not by run-derived UUIDs. That keeps editorial work stable
across re-ingests when deterministic IDs would otherwise change with pipeline
settings.

Annotations supply:

- taxonomy category lists;
- `editorial_note` summary / takeaway / supporting proposition `client_ref`s;
- `reviewer_status` (mapped into public `editorial_takeaway.status`).

## Interpretation rules

- Taxonomy tags are **human editorial interpretation**, not regulator-official
  categories unless a future source publishes equivalent labels.
- They support filtering and corpus description on Observatory.
- They must not be presented as legal conclusions or sentencing guidance.
- Missing annotation ⇒ decision is omitted from the release (builder requires
  annotated coverage for included decisions).

## Versioning

Bump `taxonomy_version` when codes are added, renamed, or retired. Update
annotations and document migration notes in the release `methodology_version` /
caveats if charts would otherwise become incomparable across releases.

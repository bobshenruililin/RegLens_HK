# Schemas and data layouts

## Relational schema (later milestones)

Canonical SQL (prepared for later milestones):
[`packages/db/migrations/001_init.sql`](../packages/db/migrations/001_init.sql).

PostgreSQL wiring remains experimental (Milestone 2B); not required for MVP-RC1
Observatory.

## Extraction schemas

| Schema | Location |
|--------|----------|
| Extraction result v2 (current) | [`packages/extraction-schema/extraction_result.v2.json`](../packages/extraction-schema/extraction_result.v2.json) |
| Extraction result v1 (legacy) | [`packages/extraction-schema/extraction_result.v1.json`](../packages/extraction-schema/extraction_result.v1.json) |
| Shared contracts | [`packages/contracts/contracts.v1.json`](../packages/contracts/contracts.v1.json) |

See also [`EXTRACTION_SCHEMA.md`](EXTRACTION_SCHEMA.md) and ADR 0001.

## Publication schemas (MVP-RC1)

Canonical public-facing contracts live under **`publications/schemas/`**:

| Schema | Purpose |
|--------|---------|
| [`publication_release.v1.json`](../publications/schemas/publication_release.v1.json) | Versioned release manifest (`release_id`, mode, caveats, file inventory) |
| [`public_decision.v1.json`](../publications/schemas/public_decision.v1.json) | Privacy-minimised decision for Observatory (no confidence / raw pages) |
| [`source_publication_policy.v1.json`](../publications/schemas/source_publication_policy.v1.json) | Per-source visibility + excerpt limits |
| [`editorial_annotations.v1.json`](../publications/schemas/editorial_annotations.v1.json) | Human taxonomy + editorial takeaway keyed by `external_ref` |

Runtime policy / taxonomy / demo annotations:

- [`publications/policies/source_publication_policy.v1.json`](../publications/policies/source_publication_policy.v1.json)
- [`publications/taxonomy/taxonomy.v1.json`](../publications/taxonomy/taxonomy.v1.json)
- [`publications/demo/editorial_annotations.v1.json`](../publications/demo/editorial_annotations.v1.json)

Release build validates inputs against these schemas. See
[`PUBLICATION_RELEASES.md`](PUBLICATION_RELEASES.md) and [`TAXONOMY.md`](TAXONOMY.md).

## Milestone 2A / local artifacts

```text
data/
  objects/sha256/ab/<sha>          # immutable raw bytes
  meta/documents/<sha>.json
  meta/spans/<sha>.json
  meta/runs/<run_key>/
    extraction.json                # immutable
    extraction.sha256
    decision.json                  # immutable pending decision view
    quarantine/                    # conflicting outputs if any
  seed/decisions/                  # reviewed decisions consumed by release build
  seed/decision.json               # mutable synthetic demo pointer (legacy/single)
```

Persistent IDs are derived from `run_key` + `client_ref` (see ADR 0002).

## Public release layout

```text
generated/public-release/
  release.json
  catalog.json
  analytics.json
  checksums.sha256
  decisions/<slug>.json
  csv/…
```

Copied for static export to `apps/site/public/data/release/` by `make pages-artifact`.
Never place `data/objects` or `private-data/` under the site public tree.

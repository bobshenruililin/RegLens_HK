# Schemas and data layouts

## Relational schema (MVP-RC2)

Canonical operational SQL:

| Migration | Purpose |
|-----------|---------|
| [`packages/db/migrations/0001_rc2_baseline.sql`](../packages/db/migrations/0001_rc2_baseline.sql) | Clean RC2 baseline (regulators → audit_events; no pgvector) |
| [`packages/db/migrations/0002_rc2_review_pending_nullable.sql`](../packages/db/migrations/0002_rc2_review_pending_nullable.sql) | Pending reviews without reviewer; expanded review statuses |

Apply with:

```bash
export REGLENS_MODE=postgres
export DATABASE_URL=postgresql://reglens:reglens_local_only@127.0.0.1:5432/reglens
make db-migrate
make db-status
```

See [`DATABASE_MIGRATIONS.md`](DATABASE_MIGRATIONS.md) and ADR 0007.

Archived experimental Milestone 2B–2D SQL (pgvector era) lives under
`packages/db/archive/` and must not be applied to RC2 databases.

## Extraction schemas

| Schema | Location |
|--------|----------|
| Extraction result v2 (current) | [`packages/extraction-schema/extraction_result.v2.json`](../packages/extraction-schema/extraction_result.v2.json) |
| Extraction result v1 (legacy) | [`packages/extraction-schema/extraction_result.v1.json`](../packages/extraction-schema/extraction_result.v1.json) |
| Shared contracts | [`packages/contracts/contracts.v1.json`](../packages/contracts/contracts.v1.json) |

See also [`EXTRACTION_SCHEMA.md`](EXTRACTION_SCHEMA.md) and ADR 0001.

## Publication schemas (MVP-RC1 — unchanged in RC2)

Canonical public-facing contracts live under **`publications/schemas/`**:

| Schema | Purpose |
|--------|---------|
| [`publication_release.v1.json`](../publications/schemas/publication_release.v1.json) | Versioned release manifest |
| [`public_decision.v1.json`](../publications/schemas/public_decision.v1.json) | Privacy-minimised decision for Observatory |
| [`source_publication_policy.v1.json`](../publications/schemas/source_publication_policy.v1.json) | Per-source visibility + excerpt limits |
| [`editorial_annotations.v1.json`](../publications/schemas/editorial_annotations.v1.json) | Human taxonomy + editorial takeaway |

Runtime policy / taxonomy / demo annotations:

- [`publications/policies/source_publication_policy.v1.json`](../publications/policies/source_publication_policy.v1.json)
- [`publications/taxonomy/taxonomy.v1.json`](../publications/taxonomy/taxonomy.v1.json)
- [`publications/demo/editorial_annotations.v1.json`](../publications/demo/editorial_annotations.v1.json)

Release build validates against these schemas for both `--input-mode demo` and
`--input-mode postgres`. See [`PUBLICATION_RELEASES.md`](PUBLICATION_RELEASES.md).

## Immutability notes

- Blobs are content-addressed by SHA-256.
- Extraction runs are keyed by deterministic `run_key`; re-ingest is idempotent.
- `extracted_propositions` are immutable; human edits create `proposition_revisions`.
- Public visibility is release membership, not a mutable `published` flag.

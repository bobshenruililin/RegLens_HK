# Documentation index — RegLens HK

Phase 0 planning package plus MVP-RC1 Observatory / MVP-RC2 Studio data-plane docs.

## Product and architecture

| Document | Description |
|----------|-------------|
| [PRD.md](PRD.md) | Product requirements (Studio + Observatory; constraints retained) |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Two-app architecture, modes, publication boundary |
| [STUDIO.md](STUDIO.md) | Studio operator guide (demo vs postgres) |
| [OPERATIONS.md](OPERATIONS.md) | Compose, workers, CI, demo pipeline |
| [OBSERVATORY.md](OBSERVATORY.md) | Public Observatory product notes |
| [PUBLICATION_RELEASES.md](PUBLICATION_RELEASES.md) | Release build, modes, scans, outputs |
| [REVIEW_WORKFLOW.md](REVIEW_WORKFLOW.md) | Accept / edit / reject / publish |
| [TAXONOMY.md](TAXONOMY.md) | Public editorial taxonomy |
| [GITHUB_PAGES.md](GITHUB_PAGES.md) | Pages workflow and manual enablement |
| [MVP_BACKBONE.md](MVP_BACKBONE.md) | Historical 2B–2D notes vs RC1/RC2 |
| [MILESTONES.md](MILESTONES.md) | Milestone status (RC2 this delivery) |

## Trust, licensing, privacy

| Document | Description |
|----------|-------------|
| [SOURCE_LICENSING_AUDIT.md](SOURCE_LICENSING_AUDIT.md) | MCHK/DCHK audit + policy enforcement note |
| [PRIVATE_DATA.md](PRIVATE_DATA.md) | Gitignored real-document layout |
| [THREAT_MODEL.md](THREAT_MODEL.md) | Concise RC2 threat model |
| [RISKS.md](RISKS.md) | Risk register including RC1 risks |
| [EXCLUSIONS.md](EXCLUSIONS.md) | Explicit non-goals |
| [ASSUMPTIONS.md](ASSUMPTIONS.md) | Assumptions and open questions |
| [`../SECURITY.md`](../SECURITY.md) | Security policy and trust boundaries |
| [`../AGENTS.md`](../AGENTS.md) | Agent / contributor hard rules |

## Schemas and evaluation

| Document | Description |
|----------|-------------|
| [SCHEMA.md](SCHEMA.md) | Relational + local artifacts; points to `publications/schemas` |
| [EXTRACTION_SCHEMA.md](EXTRACTION_SCHEMA.md) | Extraction JSON schema notes |
| [EVALUATION.md](EVALUATION.md) | Gold eval; public site = corpus description not prevalence |
| [LOCAL_SETUP.md](LOCAL_SETUP.md) | Dev setup, `apps/studio` vs `apps/site`, make targets |
| [DATABASE_MIGRATIONS.md](DATABASE_MIGRATIONS.md) | RC2 migration runner |
| [BACKUP_RESTORE.md](BACKUP_RESTORE.md) | Local dump / object-store restore notes |

## Approvals and ADRs

| Document | Description |
|----------|-------------|
| [approvals/PHASE0_APPROVAL.md](approvals/PHASE0_APPROVAL.md) | Phase 0 approval |
| [approvals/M2A_BASELINE.md](approvals/M2A_BASELINE.md) | Milestone 2A baseline |
| [approvals/MVP_RC1_BASELINE.md](approvals/MVP_RC1_BASELINE.md) | MVP-RC1 baseline |
| [approvals/MVP_RC2_APPROVAL.md](approvals/MVP_RC2_APPROVAL.md) | MVP-RC2 approval |
| [adr/0001-extraction-contract-v2.md](adr/0001-extraction-contract-v2.md) | Extraction contract v2 |
| [adr/0002-immutable-run-identity.md](adr/0002-immutable-run-identity.md) | Immutable run identity |
| [adr/0003-synthetic-private-data-boundary.md](adr/0003-synthetic-private-data-boundary.md) | Synthetic vs private-data |
| [adr/0004-studio-observatory-separation.md](adr/0004-studio-observatory-separation.md) | Studio / Observatory split |
| [adr/0005-publication-release-boundary.md](adr/0005-publication-release-boundary.md) | Publication release boundary |
| [adr/0006-static-client-search.md](adr/0006-static-client-search.md) | Static client search |
| [adr/0007-postgres-operational-source-of-truth.md](adr/0007-postgres-operational-source-of-truth.md) | Postgres SoT |
| [adr/0008-stable-decision-identity.md](adr/0008-stable-decision-identity.md) | Stable decision UUIDs |
| [adr/0009-immutable-proposition-revisions.md](adr/0009-immutable-proposition-revisions.md) | Append-only revisions |
| [adr/0010-explicit-storage-modes.md](adr/0010-explicit-storage-modes.md) | demo vs postgres modes |
| [adr/0011-publication-transaction.md](adr/0011-publication-transaction.md) | Publication transaction |
| [adr/0012-studio-auth-role-model.md](adr/0012-studio-auth-role-model.md) | Studio roles |

## Licensing outreach

- [licensing/](licensing/) — consent request drafts and outreach log

## Contributing

- [`../CONTRIBUTING.md`](../CONTRIBUTING.md)
- [`../README.md`](../README.md) — quick start

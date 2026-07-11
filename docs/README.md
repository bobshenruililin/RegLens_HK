# Documentation index — RegLens HK

Phase 0 planning package plus MVP-RC1 Observatory, MVP-RC2 Studio data-plane,
and MVP-RC3 internal source-sync / real-corpus pilot docs.

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
| [SOURCE_SYNC.md](SOURCE_SYNC.md) | RC3 policy-aware source sync |
| [SOURCE_ADAPTERS.md](SOURCE_ADAPTERS.md) | MCHK/DCHK adapter expectations |
| [CRAWL_POLICY.md](CRAWL_POLICY.md) | Live-access and no-PDF CI policy |
| [REAL_CORPUS_PILOT.md](REAL_CORPUS_PILOT.md) | Internal Core 50 pilot posture |

## Trust, licensing, privacy

| Document | Description |
|----------|-------------|
| [SOURCE_LICENSING_AUDIT.md](SOURCE_LICENSING_AUDIT.md) | MCHK/DCHK audit + policy enforcement note |
| [PRIVATE_DATA.md](PRIVATE_DATA.md) | Gitignored real-document layout |
| [THREAT_MODEL.md](THREAT_MODEL.md) | Concise RC2 threat model |
| [OCR.md](OCR.md) | OCR as internal text variants only |
| [LLM_PROCESSING.md](LLM_PROCESSING.md) | Bounded extractor/critic and real-provider gates |
| [CORRECTIONS.md](CORRECTIONS.md) | Internal corrections workflow |
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
| [EXTRACTION_EVALUATION.md](EXTRACTION_EVALUATION.md) | RC3 Core 10/Core 50 evaluation notes |
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
| [approvals/MVP_RC3_APPROVAL.md](approvals/MVP_RC3_APPROVAL.md) | MVP-RC3 approval |
| [approvals/MVP_RC3_BASELINE.md](approvals/MVP_RC3_BASELINE.md) | MVP-RC3 baseline |
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
| [adr/0013-policy-aware-source-sync.md](adr/0013-policy-aware-source-sync.md) | Policy-aware source sync |
| [adr/0014-source-versioning.md](adr/0014-source-versioning.md) | Source versioning |
| [adr/0015-ocr-text-variants.md](adr/0015-ocr-text-variants.md) | OCR text variants |
| [adr/0016-bounded-extractor-critic.md](adr/0016-bounded-extractor-critic.md) | Bounded extractor/critic |
| [adr/0017-core50-pilot.md](adr/0017-core50-pilot.md) | Core 50 internal pilot |

RC3 standing caveats: public availability is not reuse permission; robots.txt is
not a licence; MCHK remains internal-only; DCHK needs the July 14, 2018 caveat;
there is no public real release or complete de-identification claim; and
student-research letters do not unlock Pages.

## Licensing outreach

- [licensing/](licensing/) — consent request drafts and outreach log

## Contributing

- [`../CONTRIBUTING.md`](../CONTRIBUTING.md)
- [`../README.md`](../README.md) — quick start

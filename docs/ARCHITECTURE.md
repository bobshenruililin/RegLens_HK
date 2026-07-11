# System architecture

## Diagram

```mermaid
flowchart TB
  subgraph operators [Operators]
    Fixtures[Manual fixtures and manifest]
    Reviewer[Human reviewer]
    User[Authenticated researcher]
  end

  subgraph web [Next.js TypeScript]
    UI[Search filters decision pages review queue]
    API[Route handlers or thin BFF]
  end

  subgraph data [Data plane]
    PG[(PostgreSQL FTS and pgvector)]
    Obj[(MinIO or S3 originals)]
  end

  subgraph worker [Python single worker]
    Ingest[Ingest and hash]
    Parse[PDF HTML text extract]
    OCR[OCR fallback]
    Seg[Page span segmentation]
    Det[Deterministic field parsers]
    LLM[LLM provider interface]
    Val[JSON Schema and quote alignment]
    Jobs[Job runner idempotent]
  end

  Fixtures --> Ingest
  Ingest --> Obj
  Ingest --> PG
  Ingest --> Jobs
  Jobs --> Parse --> Seg
  Parse --> OCR
  OCR --> Seg
  Seg --> Det
  Det --> LLM
  LLM --> Val
  Val --> PG
  Reviewer --> UI --> API --> PG
  User --> UI
  API --> Obj
  Seg --> PG
```

## Design notes

- One worker process polls `jobs` (`FOR UPDATE SKIP LOCKED`) when the job table is wired; Milestone 1 uses a synchronous fixture ingest CLI writing a local artifact store that mirrors blob + metadata behaviour.
- LLM behind `LLMProvider.extract(doc_ctx) -> dict`; mock provider for tests and Milestone 1.
- Documents are untrusted data: prompts wrap content in delimiters; no tool-calling from document text.
- Compose services: `db` (pgvector/pg16), `minio`. Web and worker commonly run on the host in early milestones.

## Repository tree

```text
reglens-hk/
  AGENTS.md
  README.md
  LICENSE                    # product code licence; not a data licence
  docker-compose.yml
  .env.example
  docs/
    ASSUMPTIONS.md
    PRD.md
    SOURCE_LICENSING_AUDIT.md
    SCHEMA.md
    EXTRACTION_SCHEMA.md
    ARCHITECTURE.md
    RISKS.md
    EVALUATION.md
    MILESTONES.md
    EXCLUSIONS.md
    LOCAL_SETUP.md
    approvals/
    licensing/
  fixtures/
    raw/mchk/
    raw/dchk/
    manifests/
    gold/
    seed/                    # checked-in demo seeds from synthetic fixtures
  apps/
    web/                     # Next.js UI + API routes
  services/
    worker/                  # Python ingest / OCR / extract
  packages/
    db/migrations/
    extraction-schema/
  scripts/
    download_checklist.md
    hash_manifest.py
  tests/
    parsers/
    schemas/
    provenance/
```

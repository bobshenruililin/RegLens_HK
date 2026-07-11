# Product requirements document — RegLens HK

## Problem

Hong Kong professional disciplinary judgments are published as uneven PDFs/HTML.
Practitioners, researchers, and compliance teams cannot reliably search, compare,
or cite structured fields with verifiable provenance.

## Product

**RegLens HK** converts primary disciplinary materials into **structured,
temporal, evidence-linked legal data**. Every material proposition links to one
or more source spans. The system does **not** give legal advice or predict
outcomes.

## Product principle

The product must not merely summarize documents. It must convert messy primary
materials into structured, temporal, verifiable legal data. A user must be able
to inspect the exact page or paragraph supporting every material extracted
proposition (in Studio / internal views). Public Observatory surfaces short
attributed excerpts only, within publication policy limits.

## Product surfaces (MVP-RC1)

| Surface | Description |
|---------|-------------|
| **RegLens Studio** | Internal authenticated environment for ingest review, evidence inspection, and operator workflows. Not publicly hosted. |
| **RegLens Observatory** | Public, read-only, static research website. Consumes a versioned publication release. Unauthenticated. |

### Synthetic technical MVP vs real research pilot

| Posture | Meaning |
|---------|---------|
| Synthetic technical MVP | Engineering demo using `fixtures/synthetic/` and `release_mode=synthetic_demo`. Safe for Pages. |
| Real research pilot | Manually acquired real documents under `private-data/`, reviewed in Studio. Not for public republication while policy is `internal_only`. |

Do not conflate the two in UX copy or evaluation claims.

## Users (MVP)

| Persona | Jobs |
|---------|------|
| Analyst / reviewer | Ingest fixtures, review extractions, prepare releases (Studio) |
| Researcher / professional user | Browse published corpus, filter, open decision pages (Observatory) |
| Admin | Manage jobs, coverage warnings, model/prompt versions (Studio; experimental) |

## Core user journeys

1. Operator drops fixtures + manifest → system hashes, stores, queues ingest.
2. Worker extracts text (deterministic) → OCR fallback when needed → segment pages → extract structured fields → validate schema → create review items.
3. Reviewer accepts/edits/rejects propositions; only reviewed sets enter a release build.
4. Release build applies taxonomy annotations, source publication policy, privacy redaction, and writes `generated/public-release`.
5. Observatory statically exports that release to GitHub Pages (client-side explore/filter).
6. *(Studio / later)* Keyword search over published content + spans for authenticated operators.

## Observatory (public product) — RC1

**Goal:** a trustworthy public research site that describes a **published corpus**,
not an authenticated case-management system.

Required behaviours:

- Static hosting only (no Studio API, no session cookies on Pages).
- Versioned release identity (`release_id`, checksums, methodology/taxonomy versions).
- Decision pages with editorial takeaway, taxonomy categories, short evidence excerpts.
- Explore / analytics / methodology / data / compare routes as static pages.
- Explicit caveats: not legal advice; synthetic_demo labelled; counts = corpus description.
- No raw judgment files on Pages.

Out of Observatory scope: review queues, confidence scores, full page text,
private-data access, live search backends.

## Functional requirements

| ID | Requirement |
|----|-------------|
| FR1 | Ingest PDF and HTML fixtures with immutable blob + SHA-256. |
| FR2 | Deterministic text extraction; OCR only when text layer insufficient (OCR still excluded from RC1 default path). |
| FR3 | Page-level `document_spans` with stable IDs. |
| FR4 | Extract: charges, rules/code provisions, findings, legal tests (as interpretation), aggravating/mitigating factors, sanctions, costs, cited authorities, appeal status (as stated). |
| FR5 | Separate `fact` vs `interpretation`; store confidence, model version, prompt version, review status (Studio/internal only; confidence never in public release). |
| FR6 | Keyword search over published content + spans (Studio / experimental 2D). Observatory uses client-side catalog filter. |
| FR7 | Filters: regulator, profession, year, sanction type, issue category, review status (admin/Studio). |
| FR8 | Decision page with source-linked fields and coverage warnings (full evidence in Studio; excerpted in Observatory). |
| FR9 | Human-review queue; no publish without supporting spans. |
| FR10 | Idempotent, resumable, auditable jobs. |
| FR11 | Versioned publication release build with policy enforcement and privacy scan. |
| FR12 | Public Observatory static site from release artifacts only. |

## Non-functional requirements

- Auditability; schema validation; tests for parsers, schemas, provenance, and public-release safety.
- Docker Compose local stack (optional infra).
- No live source adapters in MVP.
- Provider interface so the LLM can be replaced.
- One background worker; no premature microservices.
- Fail-closed Studio production auth; no secrets in Pages artifacts.

## Preferred architecture

- Next.js + TypeScript (`apps/studio`, `apps/site`)
- Python (ingest, extraction, release build)
- PostgreSQL with FTS + pgvector (experimental / later)
- Object storage for originals (local default)
- Docker-based local development
- GitHub Pages for Observatory static export only

## Non-goals / constraints (unchanged)

See [`EXCLUSIONS.md`](EXCLUSIONS.md). Constraints that remain in force:

- No scraping / live harvest.
- No NCHK in MVP.
- No outcome prediction or legal-advice chatbot.
- No public anonymous access to **raw** judgments or Studio.
- No multi-tenant billing.
- Real public republication blocked by source publication policy until consent /
  licence posture changes (consent statuses in the licensing audit are not
  altered by engineering convenience).

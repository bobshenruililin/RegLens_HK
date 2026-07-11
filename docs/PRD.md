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
proposition.

## Users (MVP)

| Persona | Jobs |
|---------|------|
| Analyst / reviewer | Ingest fixtures, review extractions, publish |
| Researcher / professional user | Search, filter, open source-linked decision pages |
| Admin | Manage jobs, coverage warnings, model/prompt versions |

## Core user journeys

1. Operator drops fixtures + manifest → system hashes, stores, queues ingest.
2. Worker extracts text (deterministic) → OCR fallback when needed → segment pages → extract structured fields → validate schema → create review items.
3. Reviewer accepts/edits/rejects propositions; only `published` sets appear in search.
4. User searches (keyword + semantic) → opens decision → inspects field → jumps to highlighted page/quote.

## Functional requirements

| ID | Requirement |
|----|-------------|
| FR1 | Ingest PDF and HTML fixtures with immutable blob + SHA-256. |
| FR2 | Deterministic text extraction; OCR only when text layer insufficient. |
| FR3 | Page-level `document_spans` with stable IDs. |
| FR4 | Extract: charges, rules/code provisions, findings, legal tests (as interpretation), aggravating/mitigating factors, sanctions, costs, cited authorities, appeal status (as stated). |
| FR5 | Separate `fact` vs `interpretation`; store confidence, model version, prompt version, review status. |
| FR6 | Keyword (Postgres FTS) and semantic (pgvector) search over published content + spans. |
| FR7 | Filters: regulator, profession, year, sanction type, rule cited, review status (admin). |
| FR8 | Decision page with source-linked fields and coverage warnings. |
| FR9 | Human-review queue; no publish without supporting spans. |
| FR10 | Idempotent, resumable, auditable jobs. |

## Non-functional requirements

- Auditability; schema validation; tests for parsers, schemas, and provenance links.
- Docker Compose local stack.
- No live source adapters in MVP.
- Provider interface so the LLM can be replaced.
- One background worker; no premature microservices.

## Preferred architecture

- Next.js + TypeScript (web)
- Python (ingest, OCR, extraction)
- PostgreSQL with FTS + pgvector
- Object storage for originals
- Docker-based local development

## Non-goals

See [`EXCLUSIONS.md`](EXCLUSIONS.md). No scraping, outcome prediction, legal-advice chatbot, public anonymous access in MVP, or multi-tenant billing.

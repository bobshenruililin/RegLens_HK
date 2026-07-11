# Product requirements (MVP / Milestone 1 slice)

## Problem

Hong Kong professional disciplinary judgments are published as uneven PDFs/HTML.
Users cannot reliably search or cite structured fields with verifiable provenance.

## Product

**RegLens HK** converts primary disciplinary materials into structured, temporal,
evidence-linked legal data. It does not give legal advice or predict outcomes.

## Milestone 1 delivered capabilities

| ID | Requirement | Status |
|----|-------------|--------|
| FR1 | Ingest PDF/HTML fixtures with immutable blob + SHA-256 | Done |
| FR2 | Deterministic text extraction; OCR deferred | Text-layer only (M1) |
| FR3 | Page-level spans with stable IDs | Done |
| FR4 | Extract core fields via mock provider | Done (heuristic mock) |
| FR5 | Fact vs interpretation + model/prompt versions | Done |
| FR8 | Source-linked decision page + coverage warnings | Done |
| FR10 | Idempotent ingest | Done |

## Users

- Operator (fixture ingest)
- Researcher (decision detail inspection)
- Agent/contributor (bound by `AGENTS.md`)

## Non-goals for Milestone 1

Live crawling, real LLM calls, public commercial republication, NCHK, predictions.

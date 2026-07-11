# ADR 0015 — OCR text variants

## Status

Accepted (MVP-RC3)

## Context

Some source PDFs may lack reliable embedded text. OCR can help internal review
but may introduce errors and expose personal data.

## Decision

Store OCR output as a distinct text variant with provider, page, quality, and
provenance metadata. OCR is disabled by default and local-only unless a later
approval changes that. OCR spans may support reviewed extraction, but they do not
replace raw bytes or source text silently.

OCR output is internal. Public availability of a PDF is not reuse permission;
robots.txt is not a licence. MCHK stays internal-only, DCHK OCR records carry the
July 14, 2018 caveat when relevant, and student-research letters do not unlock
Pages.

## Consequences

- Reviewers can reason about OCR quality and provenance.
- Public release scanners must reject OCR/page text for real sources.
- RC3 makes no public real release and no complete de-identification claim.

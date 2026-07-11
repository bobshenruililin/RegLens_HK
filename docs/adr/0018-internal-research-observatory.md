# ADR 0018 - Internal research observatory posture

## Status

Accepted (MVP-RC4)

## Context

RC3 added policy-aware source sync and internal real-corpus pilot planning. RC4
adds public Observatory enrichment pages and internal research tooling. The
project needs a clear posture so explanatory public pages do not imply that real
MCHK/DCHK materials are approved for Pages.

## Decision

Keep the Observatory public, static, and synthetic/demo by default while using
Studio as the internal research environment for real corpus work.

- `apps/site` may explain the pipeline, research questions, and roadmap.
- Public pages must state that GitHub Pages is public.
- Real corpus acquisition, OCR, extraction, review, and interpretation remain in
  Studio/private storage.
- A public real release requires a later legal/source-policy approval and a
  checked publication release.

## Consequences

- Public education can improve without changing source-policy risk.
- Pages remains unsuitable for raw documents, real review notes, or internal
  research routes.
- Future public real release work must change policy and approval records rather
  than bypassing Studio.

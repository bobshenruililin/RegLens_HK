# RC3 OCR

OCR is an internal text-recovery aid for documents whose embedded text is absent
or poor. It is not a republication mechanism.

## Behaviour

- OCR is disabled by default.
- The Tesseract adapter is local-only and bounded by page/byte/runtime limits.
- OCR spans are stored as a separate text variant with provenance and quality
  metadata.
- OCR output must not replace source bytes or original extracted spans silently.
- Reviewers decide whether OCR text is usable for extraction evidence.

## Publication limits

OCR text may contain personal data and recognition errors. It must not be copied
to the public Observatory, public JSON, Pages artifacts, logs, or test snapshots.
Privacy scans are required at release boundaries, but they do not prove complete
de-identification.

## RC3 guardrails

- Public availability of a PDF does not grant reuse permission for OCR text.
- robots.txt is not a licence for extraction, OCR, or redistribution.
- MCHK remains internal-only for public visibility.
- DCHK OCR/evidence records must carry the July 14, 2018 publication caveat where
  relevant.
- RC3 permits no public real release.
- Student-research letters do not unlock Pages publication.

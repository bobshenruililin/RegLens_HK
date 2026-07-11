# ADR 0013 — Policy-aware source sync

## Status

Accepted (MVP-RC3)

## Context

RC3 needs live-source metadata discovery for MCHK and DCHK without weakening the
RC1/RC2 publication boundary. Official web availability is useful for discovery,
but it is not reuse permission. robots.txt is a crawler signal, not a licence.

## Decision

Source sync is policy-aware and fail-closed:

- source policies define enabled status, official hosts/paths, request budgets,
  contact requirements, acquisition mode, and public-visibility references;
- ordinary CI uses offline fixtures and does not download PDFs;
- live sync requires Postgres mode, `DATABASE_URL`, and operator contact when
  required;
- MCHK remains internal non-commercial research / `internal_only`;
- DCHK metadata carries the July 14, 2018 publication-coverage caveat.

Student-research letters are recorded as internal posture evidence only; they do
not unlock Pages or public real releases.

## Consequences

- Parser health can be checked without crawling regulator sites.
- No public real release is created by sync.
- Privacy scans remain necessary but do not prove complete de-identification.

# RC3 source sync

RC3 adds policy-aware metadata sync for official MCHK and DCHK judgment indexes.
It is an internal research capability, not a public-corpus release path.
RC4 Core10 uses source sync as the first internal step before acquisition,
extraction, review, and internal research.

## What sync may do

- Parse official index pages through source-specific adapters.
- Store metadata, hashes, parser health, and caveats in the trusted data plane.
- Run offline fixture sync in ordinary CI and local verification.
- Require explicit live prerequisites for network access: Postgres mode,
  operator contact, source policy, allow-listed host/path, request budget, and
  low concurrency.

## What sync must not do

- Treat public availability as reuse permission.
- Treat robots.txt as a licence or consent record.
- Download PDFs in ordinary CI or offline adapter smoke tests.
- Publish real MCHK/DCHK judgments, excerpts, OCR text, or page text to Pages.
- Use GitHub Pages as a controlled research environment; Pages is public.
- Claim complete de-identification; scans reduce risk but do not eliminate it.

## Workflow ladder (do not conflate)

| Workflow / command | What it does | Network | PDFs | Postgres |
|--------------------|--------------|---------|------|----------|
| **Source adapter smoke test — offline** (Actions) | Parse synthetic fixtures | No | No | No |
| **Live source health — metadata only** (Actions, manual) | Few index GETs | Yes (allow-listed) | No | No (dry-run forced) |
| `sources sync --mode metadata --live --no-dry-run` | Full metadata sync | Yes | No | Yes |
| `sources sync --mode acquire …` | Document acquisition | Yes | Yes (policy-gated) | Yes |

Ordinary CI must not require live health. External site outages must not fail PR checks.

## Source posture

- **MCHK:** internal non-commercial research posture only; public visibility stays
  `internal_only` until a separate source-policy approval changes it.
- **DCHK:** metadata discovery only by default; record the July 14, 2018 caveat
  that written judgments are generally published only where all or some charges
  were found guilty.
- Student-research letters are useful evidence for internal research posture, but
  they do not unlock GitHub Pages or any public real release.

## Operator commands

```bash
make sources-status
make source-sync-mchk-dry
make source-sync-dchk-dry
make source-parser-tests
```

Live sync/acquisition remains opt-in and policy-gated outside ordinary CI.
If operator live contact is unset, do not run live sync.

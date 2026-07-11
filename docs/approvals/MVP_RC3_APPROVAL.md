# MVP-RC3 approval

| Field | Value |
|-------|-------|
| Milestone | MVP-RC3 — Live Source Sync and Real Corpus Pilot |
| Approver | Repository owner (implementation request) |
| Approval channel | Owner RC3 implementation prompt |
| Execution timestamp (UTC) | 2026-07-11T14:47:00Z |
| Base commit (RC2 on main) | `ddf8b13` (merge of PR #10); branch `cursor/mvp-rc3-live-corpus` |

## Approved technical/product scope

The repository owner approves implementation of:

- controlled, policy-aware source synchronization;
- metadata discovery from official MCHK and DCHK judgment indexes;
- a local/internal non-commercial MCHK document-acquisition pilot path;
- DCHK metadata discovery;
- a manually controlled DCHK acquisition path;
- local OCR (Tesseract adapter; default off);
- implementation — **not** automatic activation — of a real LLM provider;
- the Core 50 internal research pilot specification and tooling;
- Studio review and research features described in the RC3 prompt.

## Explicitly not granted by this approval

This record is **technical/product approval only**. It is **not**:

- source-owner consent beyond what is already recorded in the licensing audit;
- legal advice;
- permission to ignore terms of use or robots directives;
- permission for public republication of real judgments;
- permission to change `consent_status` beyond evidence already filed;
- permission to publish real excerpts on the Observatory / Pages;
- permission to flip `source_publication_policy` away from `internal_only`.

## Continuing restrictions

- No HKLII crawling; no NCHK; no CAPTCHA/auth bypass; no headless browser;
- No high-concurrency crawling, rotating proxies, or user-agent spoofing;
- No raw real documents in Git, CI, Pages, logs, or test snapshots;
- No network LLM processing of real text without explicit runtime approval gates;
- No automatic publication; no breaking change to `publication_release.v1`;
- Do not weaken RC1/RC2 tests.

## Consent posture note (pre-existing)

Owner-reported postal letters approve **HKU student research** use for MCHK/DCHK
(see `docs/licensing/OUTREACH_LOG.md`). Public real releases remain **blocked**.
RC3 must not silently reinterpret those letters as public-release permission.

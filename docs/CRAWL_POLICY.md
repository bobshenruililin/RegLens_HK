# RC3 crawl policy

RC3 does not introduce broad crawling. It allows controlled metadata discovery
for approved source policies and explicit operator-run live checks.

## Defaults

- Ordinary CI uses offline fixtures only.
- Source health is `workflow_dispatch` only; it is not scheduled.
- No PDFs are downloaded by CI source-health checks.
- No CAPTCHA/auth bypass, headless browser, rotating proxies, or user-agent
  spoofing.
- Concurrency is one request at a time with policy-defined delay and request
  budget.

## Preconditions for live access

Live sync requires all of:

1. enabled source automation policy;
2. `REGLENS_MODE=postgres` and `DATABASE_URL`;
3. `REGLENS_HTTP_CONTACT` when policy requires contact;
4. allowed host/path, MIME type, redirect policy, byte limit, and request budget;
5. operator approval reference.

## Licence and privacy posture

- Public availability does not mean reuse permission.
- robots.txt is not a licence and does not replace source terms or consent.
- MCHK is internal non-commercial research / `internal_only` for public release.
- DCHK needs the July 14, 2018 publication-coverage caveat on discovered rows.
- No public real release is allowed in RC3.
- Privacy scans do not support a claim of complete de-identification.
- Student-research letters do not authorize Pages publication.

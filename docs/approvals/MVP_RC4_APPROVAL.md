# MVP-RC4 approval

| Field | Value |
|-------|-------|
| Milestone | MVP-RC4 — Core 10 Internal Research Launch |
| Approver | Repository owner (implementation request + technical-staff brief) |
| Approval channel | Owner RC4 prompt / co-founder technical staff conversation |
| Execution timestamp (UTC) | 2026-07-11T15:25:00Z |
| Base | `main` at merged RC3 (PR #12), tip `5a4c6ee` |

## Approved product/technical scope

- Clarify offline vs live source-health workflows;
- Core 10 internal pilot management (selection, Studio progress, report);
- Editorial handbook / codebook;
- Authenticated Studio **internal research observatory** (explore, compare, issues, sanctions, rules, authorities, coverage, collections);
- Review productivity for Core 10;
- Public Observatory enrichment using **synthetic data only** (tour, questions, roadmap);
- Explicit statement that GitHub Pages is publicly accessible and not an internal research environment.

## Not granted

- Public release of real decisions or real source text on Pages;
- Change to `source_publication_policy` / `consent_status` beyond already-recorded student-research postal approvals;
- Live crawling in ordinary CI; scheduled PDF acquisition;
- NCHK; semantic search; outcome/sanction prediction; automatic acceptance;
- Breaking `publication_release.v1`.

## Architecture reminder

```
Public GitHub Pages Observatory  → synthetic / approved public releases only
Authenticated RegLens Studio     → real corpus, review, internal research
```

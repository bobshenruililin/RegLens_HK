# LawTrace HK — agent startup routine

Path-scoped startup for agents working on LawTrace only. Do not broaden RegLens claims or couple products.

## Every LawTrace session

1. **Inspect** current branch and `git status` working tree.
2. **Run** `make lawtrace-doctor` and read its Next: line.
3. **Read** `reports/lawtrace/stage_e_final_decision.md` and `docs/LAWTRACE_OPERATIONS.md` (plus latest RC report under `reports/lawtrace/`).
4. **Identify** the smallest measurable objective (one failing gate, one broken route, one data mode).
5. **Implement** without inventing legal claims, APIs, or sources.
6. **Run** `pytest tests/lawtrace` and reconstruction/determinism-relevant checks; `make lawtrace-ci` for UI/export changes.
7. **QA** on the running site (`make lawtrace-open` / open-local): landing → comparison, search, provenance, sample labels.
8. **Update** LawTrace docs/reports when behaviour or coverage changes.
9. **Never** broaden legal claims, date semantics, or public-launch scope autonomously.

## Locked reminders

- Promise: compare two official open-data versions of a HK legislative section and inspect what changed.
- Snapshot wording: “Official open-data snapshot dated [date].”
- No force-of-law, commencement, verified-copy, or legal-importance implications.
- Cap. 599G local-real is gitignored; demo CI uses Cap. 614.
- Ordinary builds exclude the local review workspace.
- No public deploy; no LLM layer for RC1.

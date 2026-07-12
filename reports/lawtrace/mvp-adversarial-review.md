# LawTrace MVP — adversarial self-review (Phase 6)

Date: 2026-07-12  
Branch: `cursor/lawtrace-mvp-vertical-slice-8c54`

## Findings

| ID | Severity | Finding | Disposition |
|----|----------|---------|-------------|
| A1 | High | Compact `StatusNotice` omitted commencement/effective-date caveat | Fixed: compact notice always includes snapshot≠commencement language |
| A2 | High | Private audit must not appear in public/demo builds | Verified: `/audit` is `notFound()` unless `NEXT_PUBLIC_LAWTRACE_AUDIT=1`; nav link gated |
| A3 | High | Cap. 599G sampled corpus must never read as complete | Present: sampling badge `sampled N/M` + insights sampling note |
| A4 | Medium | Comparator channels were stacked headings, easy to miss status-only | Fixed: tabbed Legal text / Structure / Metadata·status; status-only callout on text tab |
| A5 | Medium | Section history loaded every transition JSON at SSG | Fixed: precomputed `change_events` + `section-histories.json` |
| A6 | Medium | Static file servers may list dirs when `index.txt` coexists | Documented: serve with index.html preference; app routes themselves are correct |
| A7 | Low | Example comparison used first available instrument only | Acceptable; Cap. 614 example remains in demo mode |
| A8 | Low | Insights lacked explicit token-flow / textual-vs-status blocks | Fixed in export + insights page |
| A9 | Info | No “human-confirmed” labels in UI/source without imported review | Confirmed absent as gold claim; audit export states not imported |
| A10 | Info | Official portal links use HKeL search URL, not fabricated deep permalinks | Acceptable Stage E posture |
| A11 | Info | Consecutive transitions only | By design |
| A12 | Medium | Working tree must commit demo (614-only) root manifest, not local mode | Remediation: regenerate `make lawtrace-web-data` before final commit |

## Trust language sweep

- Forbidden claims (“law in force on date X”, commencement/effective as version dates, verified copy, legal importance of frequency): not found in product copy.
- Mandatory disclaimer present on landing, instrument, transition, comparator, history, insights, methodology, audit.

## RegLens isolation

- No changes to `services/worker`, Studio/Site publication paths, or DB schemas in this MVP branch beyond Makefile LawTrace targets and `.gitignore`.

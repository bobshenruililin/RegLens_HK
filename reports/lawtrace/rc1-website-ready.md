# LawTrace Website RC1 — completion and review notes

**Date:** 2026-07-12  
**Branch:** `cursor/lawtrace-mvp-vertical-slice-8c54`  
**Preview:** `make lawtrace-open` → http://127.0.0.1:3010/

## Dataset

| Instrument | Coverage | Mode |
|------------|----------|------|
| Cap. 614 | 12/12 EN snapshots; reconstruction 392/392 | Complete (tracked demo + local) |
| Cap. 599G | 101/101 EN snapshots; reconstruction 3401/3401 | Complete local-real (gitignored) |

## Material fixes in this pass

1. **Critical:** Local review removed from ordinary navigation (direct `/review/` only).
2. **High:** Completeness badges show `Complete N/M` (e.g. `Complete 101/101`).
3. **High:** Metadata-only deltas (e.g. `start_period`) classified as `status_changed`, not `text_changed`.
4. **High:** Landing “Explore a real change” prefers Cap. 599G examples with non-empty legal-text redlines.
5. **Medium:** Copy page URL control; tab roving tabindex; table `scope="col"`; methodology contact placeholder replaced for private prototype.
6. **Release:** `make lawtrace-open|open-demo|open-local|doctor|stop`; Cursor rule; operations/release/startup docs; CI artifact + static smoke.

## Independent review summary

| Role | Result |
|------|--------|
| Law-student tasks | Pass after nav/CTA fixes |
| Practising-lawyer tasks | Pass (provenance, tabs, copy URL) |
| Public-health researcher | Pass (599G complete 101/101, evidence links) |
| Trust auditor | Pass for locked date/status language; review nav fixed |
| A11y / release | Medium tab focus fixed; no Pages deploy of LawTrace |

## Commands

```bash
make lawtrace-doctor
make lawtrace-open      # Cap. 599G local-real when extracts exist
make lawtrace-stop
```

## Non-blocking limitations

- Cap. 599G web artifacts remain gitignored; CI demo build marks Cap. 599G unavailable.
- Local review is not authentication.
- No public deployment; no LLM layer.
- Instrument explorer HTML for Cap. 599G is large (chunked JSON still used for transitions).

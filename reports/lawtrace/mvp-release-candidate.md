# LawTrace HK MVP — release-candidate report (Phase 8)

## 1. MVP result

**PASS WITH LIMITATIONS**

## 2. Supported product promise

Compare two official open-data versions of a Hong Kong legislative section and
inspect what changed.

Mandatory status language is present contextually (not footer-only).

## 3. Local startup (demo)

```bash
make lawtrace-web-data
cd apps/lawtrace && npm ci && npm run build
# serve static export with directory index.html preference, e.g.:
python3 -m http.server 3010 --directory out
# Prefer a handler that serves index.html for directories (see docs/LAWTRACE_MVP.md)
```

Dev mode:

```bash
cd apps/lawtrace && npm ci && npm run dev
# http://127.0.0.1:3010
```

## 4. Real-data generation

```bash
# Official EN Cap. 301–600 ZIPs → data/lawtrace/raw/
# Extract cap_599G_* members → data/lawtrace/extracted/cap599g/
make lawtrace-web-data-local
cd apps/lawtrace && NEXT_PUBLIC_LAWTRACE_AUDIT=1 npm run build
```

Default limiter: `--cap599g-max-versions 30` (even-span). Labeled **sampled, not complete**.

## 5. Production build

```bash
make lawtrace-build   # demo data + npm ci + typecheck + build
# or
make lawtrace-ci
```

## 6. Private preview URL

Not created. No documented secure private-preview path requiring no new secret
disclosure was used. Deliverable is local production build + screenshots.

## 7. Main user journeys

1. Landing → example comparison (≤3 interactions)
2. Instrument explorer (Cap. 614 / Cap. 599G when local)
3. Transition explorer (consecutive snapshots)
4. Section comparator (redline, side-by-side, channel tabs, provenance, download)
5. Section history
6. Insights (descriptive)
7. Methodology
8. Private audit (explicit env flag only)

## 8. Cap. 614 coverage

- 12 English top-level version snapshots (complete fixture corpus)
- 37 tracked top-level section @ids
- Reconstruction: 392/392 (100%) on export tests / committed artifacts

## 9. Cap. 599G coverage

- Local-real only (gitignored web artifacts)
- 101 available EN versions; default export **30 even-span** (sampled, not complete)
- Reconstruction: 981/981 (100%) on sampled export in this environment
- 43 unique section @ids in sampled set

## 10. Insights

Deterministic from export: relationship totals, textual vs status, token flow,
transition activity bars, most-changed sections (descriptive), renderability,
sampling completeness. Counts reconcile with `transitions.json`.

## 11. Reconstruction / determinism

- Cap. 614 reconstruction rate 1.0
- Cap. 599G sampled reconstruction rate 1.0
- Content hashes exclude generation timestamps (`dump_json` scrub)

## 12. Tests

- `pytest tests/lawtrace` — export, demo artifacts, prior stage tests
- App: `npm run typecheck` + `npm run build` (demo and audit-enabled local)
- Browser product review (Playwright) — screenshots under
  `/opt/cursor/artifacts/lawtrace-screenshots/`
- Accessibility: skip-link, focus-visible, multi-signal redlines, labelled tabs;
  no axe automation suite (limitation)

## 13. RegLens verification

Recorded in completion notes after `make verify` on this branch.

## 14–15. Browser + adversarial review

See `reports/lawtrace/mvp-adversarial-review.md` and screenshot artifacts.

Material fixes: compact date caveat; comparator channel tabs; section-history
precompute; public build excludes audit UI; demo vs local manifests.

## 16. Screenshots

`/opt/cursor/artifacts/lawtrace-screenshots/01-landing.png` … `11-tablet-insights.png`

## 17. Routes

- `/`
- `/instruments/[id]/`
- `/instruments/[id]/transitions/[from]/[to]/`
- `/instruments/[id]/sections/[sectionId]/`
- `/instruments/[id]/sections/[sectionId]/compare/[from]/[to]/`
- `/insights/`
- `/methodology/`
- `/audit/` (only when `NEXT_PUBLIC_LAWTRACE_AUDIT=1`)

## 18–25. Remaining sections

Filled in agent completion message (file list, diffstat, commits, limitations,
recommendation, user-testing tasks).

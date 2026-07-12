# LawTrace MVP — planned files (Phase 0)

## Worker

- `services/lawtrace-worker/lawtrace_worker/export_web.py`
- `services/lawtrace-worker/lawtrace_worker/web_schema.py`
- `tests/lawtrace/test_export_web.py`

## App (`apps/lawtrace/`)

- Next.js static export shell (`package.json`, `next.config.js`, `tsconfig.json`)
- `app/` routes: `/`, `/instruments/[id]/`, `/instruments/[id]/transitions/[from]/[to]/`,
  `/instruments/[id]/sections/[sectionId]/`, `/instruments/[id]/sections/[sectionId]/compare/[from]/[to]/`,
  `/insights/`, `/methodology/`, `/audit/`
- `lib/data.ts`, `lib/format.ts`, `lib/disclaimer.ts`
- `components/*` (chrome, disclaimer, redline, timeline, search)
- `public/data/` demo artifacts (Cap. 614)
- gitignored Cap. 599G artifacts under `public/data/instruments/cap-599g/`

## Docs / Make

- `docs/adr/0021-lawtrace-mvp-sibling-app.md`
- `docs/LAWTRACE_MVP.md`
- Makefile targets: `lawtrace-web-data`, `lawtrace-web-data-local`, `lawtrace-build`, `lawtrace-ci`

# LawTrace HK — operations guide

Concise runbook for opening, refreshing, testing, and extending LawTrace.

## Open the website

```bash
make lawtrace-doctor   # readiness report
make lawtrace-open     # prefers Cap. 599G local-real when extracts exist
```

Printed URL is typically `http://127.0.0.1:3010/` (or the next free port).

| Command | Behaviour |
|---------|-----------|
| `make lawtrace-open` | Auto: local-real if Cap. 599G XML extracts exist, else Cap. 614 demo |
| `make lawtrace-open-demo` | Cap. 614 demo only |
| `make lawtrace-open-local` | Requires Cap. 599G extracts; builds with local review workspace |
| `make lawtrace-stop` | Stops the preview server started by open scripts |
| `make lawtrace-doctor` | Dependencies, sources, generated data, build, ports |

No authentication is required for local viewing.

## Demo vs local-real data

- **Demo:** Cap. 614 complete English snapshots (tracked under `apps/lawtrace/public/data/instruments/cap-614/`). Cap. 599G marked unavailable.
- **Local-real:** Cap. 614 + complete Cap. 599G English snapshots when XML exists at `data/lawtrace/extracted/cap599g/`. Cap. 599G artifacts are **gitignored**.

Generate:

```bash
make lawtrace-web-data          # demo
make lawtrace-web-data-local    # local-real (needs extracts)
```

## Refresh Cap. 599G source extracts

Use only the approved official DATA.GOV.HK / HKeL open-data acquisition path documented in `docs/LAWTRACE_MVP.md` and fixture manifests under `fixtures/lawtrace/`. Do not scrape HKeL HTML or unofficial mirrors.

After extracts are present:

```bash
find data/lawtrace/extracted/cap599g -name '*.xml' | wc -l   # expect 101 EN snapshots when complete
make lawtrace-web-data-local
make lawtrace-open-local
```

Preserve extracts before RegLens `make verify` if that target clears `data/` (copy to `/tmp/lawtrace-preserve/cap599g`).

## Tests

```bash
PYTHONPATH=services/lawtrace-worker:services/worker pytest tests/lawtrace -q
make lawtrace-ci          # demo export + typecheck + production build + route/hygiene gates
```

Interpretation:

- Reconstruction failures → do not ship ordinary complete redlines for those pairs; fail closed.
- Hygiene failures → remove tracked ZIP/XML/Cap. 599G public data / review routes from ordinary build.
- Typecheck/build failures → fix TypeScript or missing generated Cap. 614 demo data.

## Add another instrument

1. Acquire official open-data XML via the approved process into a dedicated extract directory.
2. Extend `lawtrace_worker.export_web` instrument registry and sampling policy.
3. Export chunked manifests, transitions, sections, histories, insights.
4. Add UI collection card + search indexing without large initial payloads.
5. Add reconstruction and artifact schema tests.
6. Document completeness vs sampling prominently.

## Regenerate insights

Insights are emitted by `python -m lawtrace_worker.export_web`. Re-run the appropriate export target; do not hand-edit insight JSON. Charts and tables in the UI must link to underlying transitions/sections.

## Local review workspace

- Route `/review/` is copied into the app **only** when `LAWTRACE_LOCAL_REVIEW=1` (used by `make lawtrace-open-local` / open auto-local).
- Ordinary `make lawtrace-build` / CI must not include `/review` or `/audit`.
- Reviewer CONFIRM / REJECT / UNCERTAIN + notes persist locally in the browser and can be JSON-exported.
- Do **not** write reviewer status back into source comparison artifacts automatically.

## Preview artifact (CI)

The LawTrace GitHub Actions workflow builds the static `apps/lawtrace/out` tree. Download the workflow artifact (when configured) or rebuild locally:

```bash
make lawtrace-build
python3 scripts/lawtrace_static_server.py --dir apps/lawtrace/out --port 3010
```

Do not use plain directory listing servers: prefer `scripts/lawtrace_static_server.py` so routes resolve to `index.html`.

## Before any public launch (human gate)

See `docs/LAWTRACE_RELEASE_CHECKLIST.md`. Binding reminders:

- Locked product claim and prohibited date/legal-status language unchanged.
- No public deploy from this runbook without separate explicit approval.
- No LLM explanation layer in RC1.

## Common failure recovery

| Symptom | Fix |
|---------|-----|
| Cap. 599G missing in UI | Restore extracts; `make lawtrace-web-data-local`; rebuild |
| Port in use | `make lawtrace-stop` or set `LAWTRACE_PORT` |
| Directory listing instead of app | Use `lawtrace_static_server.py`, not bare `npx serve` without SPA config |
| Stale demo after local work | Re-run export; confirm `manifest.json` `dataset_mode` |
| `make verify` deleted extracts | Restore from `/tmp/lawtrace-preserve/cap599g` |

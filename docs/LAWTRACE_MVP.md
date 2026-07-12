# LawTrace HK Website RC1

Sibling read-only application for comparing official DATA.GOV.HK / HKeL
English legislation XML snapshots.

## Product promise

Compare two official open-data versions of a Hong Kong legislative section
and inspect what changed.

## Status language

LawTrace displays transformations of open data obtained through DATA.GOV.HK.
LawTrace output is for information and research only and is not a verified
copy of legislation. Users requiring an official verified copy should consult
Hong Kong e-Legislation.

Snapshot labels: “Official open-data snapshot dated [date]”.
They are not commencement or effective dates.

## Commands

```bash
# Demo (CI / Cap. 614 committed fixtures)
make lawtrace-web-data
make lawtrace-ci
make lawtrace-preview          # build + serve http://127.0.0.1:3010/

# Local-real Cap. 599G (complete export of all available EN snapshots)
# Prerequisites:
#   1) Official EN Cap. 301–600 ZIPs in data/lawtrace/raw/
#   2) Extracted cap_599G_* XML under data/lawtrace/extracted/cap599g/
make lawtrace-web-data-local
make lawtrace-preview-local

# Optional local review workspace (not authentication):
LAWTRACE_LOCAL_REVIEW=1 make lawtrace-build-local
```

`scripts/lawtrace_static_server.py` serves `out/` preferring `index.html`
and disables directory listings.

## Modes

| Mode | Cap. 614 | Cap. 599G |
|------|----------|-----------|
| demo (CI) | committed under `apps/lawtrace/public/data/instruments/cap-614/` | marked unavailable |
| local | regenerated | gitignored `.../cap-599g/` — **complete** when extracts exist |

## Note on `make verify`

RegLens `demo-ingest` removes the top-level `data/` directory. Re-place LawTrace
raw/extracts afterwards if you need Cap. 599G local mode again.

## Public launch

Not authorized. Do not deploy publicly. No LLM explanation layer.

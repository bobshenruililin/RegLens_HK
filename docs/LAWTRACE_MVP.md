# LawTrace HK MVP

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

## Commands

```bash
# Demo web data (Cap. 614 committed artifacts)
make lawtrace-web-data

# Local-real Cap. 599G (gitignored) after official extracts exist
# 1) Download Cap. 301–600 EN ZIPs into data/lawtrace/raw/
# 2) Extract cap_599G members into data/lawtrace/extracted/cap599g/
# 3) Export (default limiter: 30 even-span versions; omit for all):
make lawtrace-web-data-local

# App (dev)
cd apps/lawtrace && npm ci && npm run dev

# Production build (demo)
make lawtrace-build

# Local showcase with private audit UI
cd apps/lawtrace && NEXT_PUBLIC_LAWTRACE_AUDIT=1 npm run build
# Serve out/ with a static server that prefers index.html for directories
# (plain `npx serve` may show directory listings when index.txt is present).
```

## Modes

| Mode | Cap. 614 | Cap. 599G |
|------|----------|-----------|
| demo (CI) | committed under `apps/lawtrace/public/data/instruments/cap-614/` | marked unavailable |
| local | regenerated | gitignored `.../cap-599g/` |

Cap. 599G local export uses `--cap599g-max-versions 30` by default and labels
the corpus as **sampled, not complete**.

## Note on `make verify`

RegLens `demo-ingest` removes the top-level `data/` directory. Re-place LawTrace
raw/extracts afterwards if you need Cap. 599G local mode again.

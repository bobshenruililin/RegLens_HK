# LawTrace Website RC1 — three-pass QA

## Pass 1 — Engineering

| Check | Result |
|-------|--------|
| Demo export + `make lawtrace-ci` | PASS (112 pages) |
| Local-real complete Cap. 599G export | PASS (101/101, ~30s, ~52MB data) |
| Local production build | PASS (484 pages, ~16s, ~96MB out) |
| Reconstruction Cap. 614 | 392/392 |
| Reconstruction Cap. 599G | 3401/3401 |
| Review/audit routes absent in public/local default builds | PASS |
| Preview server prefers index.html | PASS (`scripts/lawtrace_static_server.py`) |
| Dedicated `.github/workflows/lawtrace.yml` | Added |
| `.gitattributes` generated markers | Added |
| Compact JSON artifacts | Enabled (non-pretty transitions/sections) |
| RegLens isolation | No RegLens domain schema changes |

Findings fixed during pass: stale `.next` audit types after route removal; example `heading` typing; missing collections page gate in CI.

## Pass 2 — Legal-data trust

Browser + route text sweep on `/`, `/methodology/`, `/insights/`, Cap. 599G:

- No unsupported “law in force on date X” claims without negation.
- Snapshot labels use official open-data wording.
- Status-only vs text channels separated; technical JSON under expandable panel.
- Complete Cap. 599G labeled Complete (not sampled).
- Frequency caveat present on history/insights.
- No human-confirmed gold claims; local review renamed and build-gated.

## Pass 3 — Product personas

Student / lawyer / policy researcher journeys exercised via Playwright:

1. Find provision via search/collections.
2. Open evidence from featured CTA (≤3 interactions).
3. Read snapshot labels + limitation.
4. Inspect provenance / official portal link.
5. Section history + insights evidence links.

All scripted checks `ok: true` in `docs/assets/lawtrace/browser-findings.json`.

## Intentionally not done

- Public deployment (prohibited).
- LLM explanation layer (prohibited by product lock / AGENTS.md).

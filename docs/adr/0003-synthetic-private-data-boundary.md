# ADR 0003 — Synthetic vs private-data boundary

## Status

Accepted (Milestone 2A)

## Context

Committing real regulator PDFs would create licensing and privacy risk. Synthetic fixtures are required for CI.

## Decision

- Tracked fixtures live only under `fixtures/synthetic/` with `fixture_kind=synthetic` in manifests.
- Real manually acquired documents live under gitignored `private-data/` with `fixture_kind=real`.
- `--demo-auto-approve-synthetic` rejects any non-synthetic row.
- CI (`scripts/check_fixtures.py`) fails if tracked manifests are non-synthetic or suspicious real PDF names appear under synthetic paths.

## Consequences

Developers can work offline with synthetic data. Real corpora never enter Git. Auto-publication of real material is blocked by construction.

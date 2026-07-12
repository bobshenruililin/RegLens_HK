# ADR 0021 — LawTrace HK MVP sibling application

## Status

Accepted for MVP vertical slice (2026-07-12).

## Context

Stage E decided **GO WITH CONDITIONS** for a version-to-version section
comparator. RegLens remains the disciplinary-decision product. LawTrace must
not couple to RegLens domain models, Studio, Pages publication, or Postgres.

## Decision

1. **Sibling Next.js static app** at `apps/lawtrace/` (`output: "export"`),
   mirroring Observatory packaging conventions without sharing domain code.
2. **Deterministic worker export** via `python -m lawtrace_worker.export_web`
   and `make lawtrace-web-data` / `make lawtrace-web-data-local`.
3. **Filesystem SoT for MVP** — no Postgres; browser loads chunked JSON only.
4. **Two data modes**
   - `demo`: Cap. 614 committed under `apps/lawtrace/public/data/`
   - `local`: Cap. 599G generated into gitignored
     `apps/lawtrace/public/data/instruments/cap-599g/`
5. **Consecutive transitions only** for the MVP comparator (reconstruction-
   proven path from Stage C).
6. **Private audit route** at `/audit/` enabled only when
   `NEXT_PUBLIC_LAWTRACE_AUDIT=1` (default off in production export unless set
   for local review).

## Consequences

- CI builds demo mode without Cap. 599G bulk text.
- Local real showcase requires one documented generation command after official
  ZIP extract.
- No public launch from this ADR; local production build only.

## Acceptance criteria (measurable)

- Cap. 614 demo export deterministic (content hashes stable).
- Reconstruction remains 100% for displayed Cap. 614 same-ID pairs.
- Production `npm run build` succeeds for `apps/lawtrace`.
- `make verify` remains green without RegLens domain edits.
- Landing → instrument → transition → comparator in ≤3 interactions.
- Mandatory disclaimer visible on landing and comparator.
- No raw ZIP/bulk XML tracked; no “human-confirmed” without imported review.

# LawTrace Website RC1 — baseline review (pre-edit)

Date: 2026-07-12  
Branch: `cursor/lawtrace-mvp-vertical-slice-8c54` @ `00d9b4a`

## Command results (executed, not asserted from Markdown)

| Command | Result |
|---------|--------|
| `pytest tests/lawtrace` | **32 passed** (~12s) |
| `make lawtrace-ci` | **OK** (~16s); demo static export |
| `npm run typecheck` (apps/lawtrace) | **OK** |
| `make verify` | **OK** (~43s; RegLens demo gate) |

## Cap. 599G complete export probe

| Metric | Value |
|--------|-------|
| Versions | 101/101 complete |
| Export time | ~30s |
| Output size | ~60 MB |
| Transitions | 100 |
| Reconstruction | 3401/3401 (100%) |
| Largest file | `sections.json` ~1.4 MB |

**Decision:** use complete Cap. 599G in local-real mode (no sample limiter by default).

## Product baseline findings (severity)

| ID | Sev | Finding |
|----|-----|---------|
| B1 | High | Landing leads with disclaimer wall; weak product-first hierarchy |
| B2 | High | Status/structure channels render raw JSON |
| B3 | High | Added/removed relationships skipped in comparator SSG |
| B4 | Med | `/audit` still emits a static path in public builds (404 page); flag named like privacy |
| B5 | Med | Cap. 599G absent in demo build (expected); local preview needs reliable serve |
| B6 | Med | Nav lacks Explore/Collections mode badges; shows Cap links + Audit |
| B7 | Med | No dedicated LawTrace CI workflow |
| B8 | Med | No `make lawtrace-preview` with correct index.html serving |
| B9 | Low | Human-readable snapshot labels secondary to filenames in places |
| B10 | Low | Generated Cap. 614 JSON is a large PR diff without `.gitattributes` markers |

## Locked constraints for RC1

- No public launch
- No LLM explanation layer (contradicts product lock / AGENTS.md)
- Keep deterministic pipeline, claim, date semantics, @id identity, provenance

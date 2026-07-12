# Stage B — Identity matrix (Cap. 614 English)

## Metrics

| Metric | Value |
|--------|-------|
| Consecutive version pairs | 11 |
| Ordinary successor coverage | **1.0000** (392/392) |
| Automatic `@id` gold-edge precision | **1.0000** (392 edges, 0 errors) |
| Matched by `@id` | 392 |
| Matched by `@temporalId` | 0 |
| Matched by unique num | 0 |
| Added | 6 |
| Ambiguous | 0 |
| Unmatched old | 0 |
| Text changed (accepted) | 34 |
| Status changed (accepted) | 34 |
| Renumber candidates | 0 |

## Scope

- Temporal identity limited to **top-level sections**.
- Nested subsections/paragraphs are content inside section versions (no independent identities).
- Schedules: **0** in Cap. 614 fixtures (experimental category unused here).

## Gold succession set

`fixtures/lawtrace/gold/cap_614_section_successions.jsonl` contains all accepted edges.
Verification method: for every consecutive pair, every older section `@id` uniquely matched the same `@id` in the newer file with zero ambiguous candidates. Spot-checked raw XML open tags confirm stable ids (e.g. section 1 `ID_1438403528606_002` across all 12 files).

## Renderability

{'complete': 429}

All Cap. 614 sampled section versions classified `complete` in Stage B (no tables/images/forms detected in section subtrees). Superscript/subscript detection remains enabled for later stages.

## Product implication

Stage B identity gate **PASS** for Cap. 614 English top-level sections under `@id` matching.

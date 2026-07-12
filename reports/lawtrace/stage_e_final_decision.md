# LawTrace HK — Stage E final feasibility decision

**Date:** 2026-07-12  
**Branch:** `spike/lawtrace-diff-stress`  
**Stages executed:** C (Cap. 614 deterministic comparison), D (Cap. 599-family probe + stress), E (this decision)

---

## 1. Decision

**GO WITH CONDITIONS**

Conditions:

1. Product claim remains the locked version-to-version comparator only.
2. Cap. 614 English top-level `@id` lineage is the primary supported pilot scope.
3. Cap. 599G is the recommended public-showcase instrument; Cap. 599J is the technical stress instrument.
4. Candidate/provisional succession edges remain algorithm-generated / agent-reviewed until independent human audit completes.
5. Ordinary complete redlines only for `renderability=complete` (and explicitly limited for `complete_with_nontext_metadata`).
6. No claim of “law in force on date X”; no verified-copy claim; no legally conclusive auto-match claim.
7. Sibling LawTrace package only — no RegLens domain coupling; no production UI/deploy in this spike.

---

## 2. Exact supported product promise

> Compare two official open-data versions of a Hong Kong legislative section and inspect what changed.

Supported meaning:

- Inputs are consecutive official DATA.GOV.HK / HKeL English XML instrument versions.
- Comparison is section-scoped for top-level sections with stable `@id`.
- Outputs show exact canonical A/B text/structure/metadata channels, provenance, and deterministic diffs.

## 3. Exact prohibited product claims

Do **not** claim:

- that displayed text was necessarily the law in force on a selected date;
- that source version dates are commencement or effective dates;
- that LawTrace output is a verified copy of legislation;
- that an automatically matched structural event is legally conclusive;
- population prevalence from corpus counts;
- split/consolidation/fuzzy succession as confirmed identity.

## 4. Supported instrument and provision types

| Scope | Support |
|-------|---------|
| Cap. 614 EN top-level sections with `@id` | Supported (Stage C gate passed) |
| Cap. 599G EN top-level sections with `@id` | Recommended showcase (Stage D) |
| Cap. 599J EN top-level sections with `@id` | Technical stress (Stage D passed) |
| Nested subsection/paragraph identity | Not independently identified |
| Schedules as first-class provisions | Experimental / out of MVP promise |

## 5. Unsupported structures and temporal events

Unsupported or candidate-only:

- split / consolidation;
- identity where `@id` changes;
- ambiguous renumbering;
- fuzzy semantic similarity;
- inferred succession without `@id`;
- `potentially_lossy` / `unsupported` renderability as ordinary complete redlines;
- “in force on date X” temporal UX.

Observed nontext metadata (`sup`/`sub`) → `complete_with_nontext_metadata` (limited ordinary redline note).

## 6. Cap. 614 results (Stage C)

| Metric | Value |
|--------|------:|
| Versions | 12 |
| Comparisons | 398 |
| Unchanged | 343 |
| Text changed | 15 |
| Status changed | 13 |
| Text+status | 21 |
| Added | 6 |
| Removed | 0 |
| Supported same-ID pairs | 392 |
| Reconstruction success | **392/392 (100%)** |
| Determinism (2 runs) | **PASS** |
| Renderability | all `complete` (784 observations) |
| Gate | **PASS** |

Evidence: `reports/lawtrace/stage_c_result.md`, `stage_c_evidence_packet.md` / `.html`, `stage_c_comparisons.jsonl`.

## 7. Cap. 599-family results (Stage D)

Bounded probe (max 40 versions/instrument, even-span sampling):

| Instrument | Files | Eval | @id coverage | Changed | Ambiguous | Recon | Score | Notes |
|------------|------:|-----:|-------------:|--------:|----------:|------:|------:|-------|
| cap:599G | 101 | 40 | 0.9894 | 148 | 0 | 1.0 | 91.27 | 100% complete |
| cap:599F | 125 | 40 | 0.9867 | 171 | 0 | 1.0 | 89.90 | some nontext metadata |
| cap:599J | 231 | 40 | 0.9940 | 134 | 0 | 1.0 | 88.09 | highest coverage |

Archive extract integrity: current 3 accepted / past 454 accepted / collisions 0 (599J+F+G filter). Parent ZIP SHA-256 matched registry.

## 8. Stress-test and showcase recommendation

- **Technical stress:** Cap. **599J** (25-version span): 115 changed pairs (≥30 target), 1203 unchanged, 16 added, 13 removed/unmatched, 0 ambiguous, reconstruction **1318/1318**, stress_pass **True**. Peak tracemalloc ~38 MB; ~65 s.
- **Public showcase:** Cap. **599G** — highest composite score, fully `complete` renderability, zero ambiguous events.

## 9. Identity precision/coverage (epistemic classes)

| Class | Cap. 614 | Cap. 599 stress (599J) |
|-------|----------|-------------------------|
| Algorithm-generated `@id` matches | 392 consecutive same-ID pairs; 100% reconstruction | 1318 matches; coverage ~99.0% of old slots |
| Agent-reviewed candidate gold | Cap. 614 provisional JSONL (`human_review_status=not_reviewed`) | None |
| Human-confirmed | **None** | **None** |

Do not report algorithm matches as human gold.

## 10. Reconstruction success

- Cap. 614: **100%** supported pairs.
- Cap. 599J stress: **100%** (1318/1318).
- Cap. 599F/G probes: **100%**.

Invariant: `apply(diff(A,B), canonical(A)) == canonical(B)` on full token stream.

## 11. Determinism results

Cap. 614 two full corpus runs:

- canonical hashes identical;
- artifact hashes identical;
- diff operation sequences identical;
- classifications identical;
- **PASS**.

## 12. Renderability distribution

- Cap. 614: 100% `complete`.
- Cap. 599G probe: 100% `complete`.
- Cap. 599J stress: mostly `complete`, minority `complete_with_nontext_metadata` (sup/sub).

## 13. Performance and resource results

| Workload | Elapsed | Peak tracemalloc | Notes |
|----------|--------:|-----------------:|-------|
| Cap. 614 full Stage C | ~1.4–4.6 s | modest | 12 versions |
| Cap. 599J stress (25 vers.) | ~65 s | ~38 MB | limiter documented |
| Cap. 599G/F/J probes (40 vers.) | ~46–50 s each | ~37 MB | even-span limiter |

ZIP download limits unchanged (`ResourceLimits` in `limits.py`). Stage D version limiters: probe 40, stress 25.

## 14. Source-provenance completeness

Each comparison carries:

- instrument; version A/B file ids; `@id`; section numbers;
- file SHA-256; archive SHA-256 when known;
- canonical hashes; comparator + normalization versions;
- renderability; official portal pointer.

## 15. XSD validation status

HKLM entrypoint XSD pinned in Stage A/B with published checksum match. **Full offline validation remains incomplete** because external W3C/DC/XHTML/MathML imports are outside the allowlist. Do not claim full schema-validated ingest.

## 16. Attribution and legal-status wording

Mandatory wording used in Stage C/D evidence packets and this report:

> LawTrace displays transformations of open data obtained through DATA.GOV.HK. LawTrace output is for information and research only and is not a verified copy of legislation. Users requiring an official verified copy should consult Hong Kong e-Legislation.

Attribution: Government / Department of Justice / HKeL / DATA.GOV.HK; Terms v1.2 referenced in `fixtures/lawtrace/ATTRIBUTION.md`.

## 17. Remaining source-rights questions

- Exact attribution string for product UI (counsel).
- Whether Cap. 599-family extracts may ever be redistributed beyond gitignored bulk (currently: no).
- Dictionary PDF reprint limits.
- Student-research letters do not unlock public real release (RegLens policy; analogous caution).

## 18. Data-quality and security findings

- ZIP path-normalization collision hardening present; Cap. 599 GIF rejection reconciled (not silent overwrite).
- XXE-safe parse via `defusedxml`.
- No raw ZIP committed; extracts under gitignored `data/lawtrace/`.
- No private council data used.
- Status-only changes are not labeled as textual amendments.

## 19. Proposed MVP architecture

- Sibling package `services/lawtrace-worker` (canonical → compare → reports).
- Filesystem fixtures for Cap. 614; gitignored bulk for Cap. 599-family.
- Deterministic token canonicalization + `difflib.SequenceMatcher(autojunk=False)`.
- Static Markdown/HTML evidence packets only (no Studio/Pages integration).
- Continue `VERSION_TO_VERSION_COMPARATOR_ONLY` date posture.

## 20. Explicit MVP exclusions

- LLM matching/explanation; embeddings; graph DB;
- production UI; auth; deploy;
- HKeL scraping; verified PDF rehost;
- RegLens schema/publication/Studio/site changes;
- auto-accept of ambiguous identity;
- “in force on date” product mode.

## 21. Estimated implementation milestones (technical, not calendar)

1. **MVP-0:** Package Cap. 614 comparator CLI + evidence export (largely done in spike).
2. **MVP-1:** Cap. 599G showcase pack (bounded versions) + human audit of sample edges.
3. **MVP-2:** Read-only local viewer (still not Pages/Studio) with disclaimer chrome.
4. **MVP-3:** Policy/counsel pass on attribution + public hosting decision.
5. **MVP-4:** Optional Postgres store for LawTrace objects — only after coexistence ADR.

## 22. Criteria before public launch

- Independent human review of audit packet / showcase edges.
- Counsel-approved attribution + legal-status chrome.
- Pages/public host decision that does not ship raw XML/PDF bytes.
- Ordinary redline gate remains fail-closed for lossy/unsupported.
- RegLens coexistence lock still held.
- No broadening of temporal claims without new evidence.

## 23. Five representative comparison artifacts

1. Cap. 614 unchanged — `reports/lawtrace/stage_c_evidence_packet.md` (Example unchanged).
2. Cap. 614 textually changed — same packet (text_changed examples).
3. Cap. 614 status-only — same packet.
4. Cap. 614 added section — same packet.
5. Cap. 599J stress examples — `reports/lawtrace/stage_d_stress_examples.md` (+ Cap. 599G probe examples).

## 24. Recommended next product experiment

Ship a **local Cap. 614 + Cap. 599G “two-version section inspector”** demo (static packet → optional thin local viewer) that only:

- picks two official EN versions;
- lists top-level sections by `@id`;
- shows three-channel diff + provenance + disclaimer;

Then run a human audit on ≥30 Cap. 599G changed pairs before any public hosting discussion.

---

## Test commands and results (Stages C–E)

```text
make verify                                          # before: 136 passed, 2 skipped (demo gate)
pytest tests/lawtrace                                # after Stage C: 23 passed; + Stage D scoring
PYTHONPATH=services/lawtrace-worker python -m lawtrace_worker.stage_c
PYTHONPATH=services/lawtrace-worker python -m lawtrace_worker.run_stage_d
```

RegLens domain paths: **unchanged**.

## Unresolved issues

- Full HKLM XSD import closure still incomplete.
- Cap. 599 `@id` coverage slightly below 100% due to real add/remove events in sampled spans (not ambiguity).
- No human-confirmed gold yet.
- GitHub Pages enablement is an operator setting (separate from this spike).

## Proposed first MVP milestone

**MVP-0.1 — Cap. 614 section comparator evidence pack + Cap. 599G showcase shortlist**, human audit kickoff, still no production UI and no RegLens coupling.

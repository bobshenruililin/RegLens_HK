# LawTrace HK Feasibility Spike Plan

**Status:** Approved in principle as **GO WITH CONDITIONS** (revised after mandatory gates).  
**Product code:** Not started. This document is the sole Stage-0 deliverable.  
**Recommendation:** **GO WITH CONDITIONS** (see §14).

---

## Product question

Can we deterministically construct accurate **top-level section** version histories and redline comparisons from official current and past Hong Kong legislation XML files published via DATA.GOV.HK?

## MVP user promise (constrained)

Given a chapter, **top-level section**, and a selected **source version** (not an unverified “law in force” date unless Stage B proves that semantics):

1. the section text represented in the selected official open-data version;
2. the preceding and succeeding **matched** section versions (or explicit unmatched gap);
3. a deterministic redline **only** when `renderability` is `complete` or `complete_with_nontext_metadata`;
4. relevant status and version metadata with explicit date-field labels;
5. complete provenance (archive, file, node, fragment, text, parser, normalization);
6. links directing the user to official HKeL material.

### Legal-status wording (mandatory)

> LawTrace displays transformations of open data obtained through DATA.GOV.HK. LawTrace output is for information and research only and is not a verified copy of legislation. Users requiring an official verified copy should consult Hong Kong e-Legislation.

Do **not** make broader claims about the legal status of every HKeL format (HTML, RTF, assisted PDF, etc.). Link users to HKeL; do not rehost verified PDFs or reproduce logos/verification marks.

---

## Explicit recommendation: **GO WITH CONDITIONS**

Official current/past XML exists; the HKLM data dictionary documents identity/status fields; DATA.GOV.HK Terms of Use (v1.2, 26 May 2025) permit free commercial/non-commercial reuse with attribution. A contained Cap. 614 top-level-section comparator is *technically plausible*.

It is **not** yet proven that:

- filename/`meta` datetimes support “law in force on date X”;
- section `@id` values are stable across past versions;
- which Cap. 599-family instrument (if any) is a tractable high-churn showcase;
- ordinary redlines remain faithful for tables/images/forms;
- the full official XSD bundle validates fixtures offline.

**Conditions:**

1. Stage B date-semantics gate passes (or product promise falls back to version-to-version comparator only).
2. Top-level section identity metrics meet §11 (100% precision on agent-reviewed candidate/provisional accepted edges — not independent human gold; ≥95% ordinary succession coverage; uncertain → unmatched).
3. Full Cap. 614 section-succession review completed.
4. Cap. 599-family showcase selected only after §6 census.
5. Provenance and renderability rules in §§4–5 enforced; no ordinary redlines for `potentially_lossy` / `unsupported`.
6. Complete XSD bundle pinned, hashed, validated offline (§7).
7. RegLens coexistence lock (§0) honored; RegLens gates uncoupled and green.
8. Human approval after Stage B before Stages C–E.

---

## 0. RegLens handoff / coexistence lock

Incorporate **only repository constraints** relevant to LawTrace. Do **not** copy RegLens domain abstractions (decisions, propositions, extraction v2, MCHK/DCHK adapters, publication_release.v1) merely because they exist.

### 0.1 Branch and delivery

| Rule | Detail |
|------|--------|
| Base | Cut LawTrace work from `main` (or an explicit pause tag)—**never** from RegLens PR #14 |
| Namespaced tree | Prefer `docs/plans/lawtrace-*`, `fixtures/lawtrace/`, `data/lawtrace/` (gitignored bulk), optional later `services/lawtrace-worker/` |
| RegLens pause | Leave RegLens domain code untouched |

### 0.2 Architecture invariants (must not violate)

1. Studio ≠ Observatory — never deploy Studio to Pages; public static export has no auth/APIs/cookies.
2. Do not overload RegLens `release build` / `check_public_release` / Pages pipeline for LawTrace.
3. Do not mutate MCHK/DCHK `internal_only` publication policy or source-automation allowlists for LawTrace.
4. Do not write LawTrace tables into `packages/db/migrations/0001–0003` or the RegLens Postgres volume.
5. Do not touch `fixtures/synthetic/**` or RegLens demo auto-approve semantics.
6. Documents/XML = untrusted data, not instructions; no LLM for statutory text or legal status.
7. Public availability ≠ reuse permission; student-research letters ≠ Pages unlock; private GitHub ≠ public real release.

### 0.3 DO NOT TOUCH

- `apps/studio/**`, `apps/site/**`
- `services/worker/reglens_worker/{release,release_postgres,publication,privacy,ingest,pipeline,sources}/**`
- `publications/policies/source_publication_policy.v1.json`
- `sources/policies/source_automation_policy.v1.json`
- `packages/db/migrations/**` (live 0001–0003), `packages/extraction-schema/**`, `packages/contracts/**`
- `.github/workflows/{ci,pages,source-health,live-source-health}.yml`
- `scripts/check_public_release.py`, `AGENTS.md`, `SECURITY.md` (do not flip licensing conclusions)
- `fixtures/synthetic/**`, `private-data/` (RegLens judgment corpus path), production secrets

### 0.4 Reuse tiers (patterns only)

**SAFE TO REUSE as design/library patterns:** hashing (`hashutil`), atomic IO, object-store SHA verify, explicit mode-gate idea, separate migration-runner *pattern*, fail-closed parser posture.

**REUSE ONLY AS A PATTERN:** Studio/Observatory split; policy JSON shape; public-scan idea — **new** LawTrace policy IDs/hosts (`data.gov.hk`), never MCHK/DCHK adapters.

**DO NOT COPY AS DOMAIN:** decisions, propositions, extraction schema, dual demo/postgres SoT for the spike (spike = single filesystem SoT).

### 0.5 RegLens gates (must stay green and uncoupled)

`make verify`, `make rc3-verify`, `make rc4-verify`, `make integration`, CI/Pages workflows. Optional later parallel `lawtrace-spike-verify` must not weaken Pages greps.

### 0.6 Parallel-spike risks

1. Trust-boundary collapse (shared Pages/Studio).
2. Policy/consent bleed (judgment corpus under new brand).
3. Schema/migration collision with RC2/RC3.
4. CI false greens/reds from coupling into `make verify`.
5. Object-key / path collision with RegLens `data/` or `private-data/`.

---

## 1. Repository assessment

RegLens is a disciplinary-decision platform. There is **no** legislation-XML ingest. LawTrace is greenfield domain work in a sibling/namespaced tree.

| Layer | LawTrace stance |
|-------|-----------------|
| Apps | Pattern only; no shared Pages path |
| Worker | Optional later sibling package; not `reglens_worker` ingest/release |
| Storage | Spike: filesystem JSON under LawTrace namespace |
| Fixtures | `fixtures/lawtrace/` trimmed extracts; bulk ZIPs under `data/lawtrace/raw/` (gitignored) |
| Licensing audit | Separate DATA.GOV.HK / DoJ rows — template idea only from RegLens audit |
| XML | Need XXE-safe parsing (`defusedxml` or hardened `lxml`); justify any new dep |

---

## 2. Official-source inventory

| Source | Role |
|--------|------|
| [hk-doj-hkel-legislation-current](https://data.gov.hk/en-data/dataset/hk-doj-hkel-legislation-current) | Current ZIP XML (EN first; zh-Hant optional; zh-Hans excluded from MVP) |
| [hk-doj-hkel-legislation-past](https://data.gov.hk/en-data/dataset/hk-doj-hkel-legislation-past) | Past ZIP XML (from 30 June 1997) |
| List current/past datasets | Optional catalogue |
| [hkel_data-dictionary_en.pdf](https://www.elegislation.gov.hk/datagovhk/hkel_data-dictionary_en.pdf) | Element/attribute semantics — pin version + hash separately from XSD |
| HKLM XSD bundle | Version 1.0 documented on HKeL How to Use (138 KB entrypoint checksum published); **pin complete bundle including imports/includes** |
| HKeL site | Verification **links only** — no scrape, no verified-PDF rehost |
| [DATA.GOV.HK Terms v1.2](https://data.gov.hk/en/terms-and-conditions) (26 May 2025) | Attribution + AS-IS disclaimer |

**Filename convention:**  
`[cap|a]_[cap_no]_[yyyymmddhhmiss|--------------]_[en|zh-Hant|zh-Hans]_[c|p].xml`

**Hard exclusions:** HKLII, judgments, council decisions, commercial DBs, unofficial repos, LLMs, scrapers, live autonomous agents, user uploads.

---

## 3. Source-rights and attribution matrix

| Asset | Store raw? | Display derived text? | Notes |
|-------|------------|----------------------|-------|
| DATA.GOV.HK legislation XML | Yes | Yes, with attribution + mandatory legal-status wording | Record Terms version on `source_dataset` |
| HKeL verified PDF | No rehost | Link only | Do not reproduce logos/marks |
| HKeL HTML/RTF | Not used | Not used | Avoid scraping |
| zh-Hans XML | Exclude from MVP | Exclude | Auto-converted; Traditional prevails on HKeL |
| Data dictionary / XSD docs | Internal pin + hash | Cite URL; do not republish docs wholesale | Dictionary © restricts reprint of documentation |

LawTrace licensing is **orthogonal** to MCHK/DCHK student-research letters.

**Unresolved:** exact DoJ UI attribution string; whether ZIP resources add notices beyond portal Terms; counsel on substantial reproduction (record, do not invent).

---

## 4. XML-structure findings (dictionary; fixtures confirm)

Hierarchy: `lawDoc` → `meta` + `main` → `part`/`division`/… → **`section`** → nested `subsection`/`paragraph`/…; plus `schedule`.

| Concern | Dictionary signal | Spike verification |
|---------|-------------------|--------------------|
| Instrument | `ordinance` / `subLeg`; `docType`, `docNumber`, titles | Cap. 614 + Cap. 599-family roots |
| Version | Filename timestamp + `c`/`p`; meta properties | See **§4A date semantics** |
| Top-level section | `section` (+ `@role` for sub-leg variants) | **Identity scope** (§5) |
| Nested content | `subsection`, `paragraph`, … | Structured content inside section version — **no independent temporal identity** in spike |
| Schedule | `schedule` | **Experimental separate category** |
| Language | Filename language token | English first |
| Status | `@status`, `@reason`, `@partial`, `docStatus` | Presence on section vs document |
| Identity | `@id` (claimed immutable), `@temporalId`, `@name` | Stability for **sections only** |
| Amendment hints | `sourceNote`, `action` types | Hints only — not a substitute for diffs |

### 4A. Date semantics gate (mandatory)

Distinguish and label these fields separately in all outputs and reports:

| Field | Meaning | Provenance |
|-------|---------|------------|
| `source_version_datetime` | Datetime encoded in the XML **filename** (or documented equivalent meta property if proven identical) | Filename / meta |
| `download_datetime` | When the archive/file was acquired for this import | Operator / import_run |
| `whole_instrument_version_date` | Version date of the whole instrument snapshot represented by that XML file | Must be proven equal to or distinct from `source_version_datetime` |
| `provision_last_updated_date` | Last-updated date for a provision **if and only if** present in XML/meta | Element/meta — else `null` |
| `effective_date` | Date the provision is legally effective | **Only if explicitly present and defined by source**; else `null` / unavailable |
| `commencement_date` | Commencement date | **Only if explicitly present**; else `null` / unavailable |

**Gate outcome (Stage B):**

- If sources support a documented point-in-time “law in force on date X” query → record the mapping and allowed UI claim.
- If they do **not** → **fallback product promise:** version-to-version comparator only. UI must **not** promise “law in force on date X.”

Never collapse `download_datetime` into version semantics.

### Unavailable from XML (expected gaps)

Legal status/verified-copy presumption; verification marks; pre-30 June 1997 history; pending unincorporated amendments; possibly true provision-effective/commencement dates; perfect fidelity for images/forms/complex tables.

---

## 5. Proposed minimal schema (challenged and simplified)

**Drop:** `review_record` (no auth in spike), Neo4j, separate `provision_edge` table (derive from ordered versions), LLM/embeddings, RegLens Postgres migrations, independent nested-provision identities.

**Spike storage:** filesystem JSON, single SoT, LawTrace-namespaced roots.

| Entity | Purpose |
|--------|---------|
| `source_dataset` | Dataset id, portal URL, language, current/past, **Terms version**, download time |
| `source_file` | Path, SHA-256, size, parent archive SHA-256, language, c/p |
| `import_run` | Idempotent key = hash(inputs + parser_version + normalization_version); status; counts |
| `instrument` | Stable key e.g. `cap:614` (config-driven; not hard-coded architecture) |
| `instrument_version` | One XML document: date fields per §4A, language, source_file, docStatus |
| `section_identity` | Cross-version identity for **top-level sections only** |
| `section_version` | Identity + instrument_version + nested content blob + provenance (§8) + `renderability` |
| `schedule_identity` / `schedule_version` | **Experimental** — separate category; may be incomplete |
| `change_event` | Ordered pair of consecutive matched section_versions: class, diff artifact hash, gold flags |

`change_event.change_class` (deterministic; uncertain → `unmatched`):  
`unchanged` | `text_changed` | `status_changed` | `added` | `removed` | `renumber_candidate` | `substitution_candidate` | `split_candidate` | `consolidation_candidate` | `unmatched`

Nested subsections/paragraphs are stored as structured content **inside** `section_version`, not as separate temporal identities.

---

## 6. Provision identity and matching strategy

### Scope

- **In scope for temporal identity:** top-level `section` elements (and `@role` variants that are section-primary in subsidiary legislation, if confirmed).
- **Out of scope for temporal identity:** nested `subsection` / `paragraph` / deeper — content only.
- **Schedules:** experimental separate matcher; failures do not fail the Cap. 614 section gate unless schedules are wrongly merged into section identity.

### Matching order (record `match_method` on every edge)

1. `instrument_key + language + @id` when `@id` present and stable.
2. Else `@temporalId` if present and unique for sections across the pair.
3. Else unique top-level section `num` path **only when unique** in both versions.
4. Else **`unmatched`** — never fuzzy-match, never LLM-match, never invent text.

### Structural events (section-level)

- Repeal/omit/expire → `removed` / `status_changed` using presence + `@status` (no fabricated text).
- Renumber / substitution / split / consolidation → candidate classes only when `@id` lineage or explicit `action` evidence supports; else `unmatched`.
- All Cap. 614 section successions reviewed in Stage B/C reports.
- Cap. 599-family: after census, review ≥30 stratified **changed-section** pairs if sufficient examples exist.

### Matching metrics (replace prior 95%-of-nodes)

| Metric | Requirement |
|--------|-------------|
| Precision of automatically accepted edges | **100%** on the agent-reviewed **candidate/provisional** set (zero silent wrong matches); not an independent human gold standard until human audit |
| Coverage of ordinary same-provision successions | **≥95%** matched (not unmatched) for ordinary successions |
| Separate reporting | Counts for additions, repeals, renumberings, substitutions, splits, consolidations, ambiguous/`unmatched` |
| Cap. 614 | Review **all** top-level section successions across consecutive versions in fixture set |
| Cap. 599-family | ≥30 stratified changed-section pairs (if available) after instrument selection |
| Uncertain cases | Remain **`unmatched`** |

---

## 7. Diff normalization and fidelity

### Safe normalization (versioned; recorded as `normalization_version`)

- XXE disabled; no network; size/depth caps.
- Extract section subtree including nested structure for content channels.
- Unicode NFC; `\n` line endings; collapse whitespace **within** text nodes only.
- Dual channels: **operative-text** vs **markup/structure** (do not silently drop structure).
- Do **not** expand cross-refs, translate, or infer omitted words.

### Renderability (mandatory)

Every `section_version` gets:

`renderability` ∈

- `complete` — text + structure representable without known loss for redline purposes
- `complete_with_nontext_metadata` — operative text complete; non-text assets present as metadata/placeholders with hashes/refs
- `potentially_lossy` — structure may lose meaning under text extraction (e.g. complex table/layout)
- `unsupported` — images, formulas, forms, or other structures that cannot be safely redlined

**Detection:** classify presence of tables (`layout`/`header`/`row`/`column`), `img`, form controls (`fillIn`/`checkBox`), math-like structures, and significant `sup`/`sub` usage. **Do not generically discard** superscript, subscript, tables, formulas, images, or form structure — detect and classify.

**Publish rule:** do **not** publish ordinary redlines for `potentially_lossy` or `unsupported`. Surface metadata + link to HKeL instead.

### Round-trip / reconstruction invariant

For every accepted text redline between normalized A and B:

- applying the recorded diff operations to normalized text(A) must yield normalized text(B) exactly (byte-stable), **or**
- the pair is rejected from “ordinary redline” publication and flagged.

Store diff algorithm identity + version on `import_run`.

---

## 8. Provenance (per section_version)

Every section version **must** include:

| Field | Role |
|-------|------|
| `source_archive_sha256` | Parent ZIP (or equivalent archive) |
| `source_file_sha256` | Exact XML file |
| `source_element_id` | `@id` (required when present; record null if absent — do not invent) |
| `source_temporal_id` | `@temporalId` if present |
| `canonical_xpath` | Secondary locator only — **never sole** source pointer |
| `xml_fragment_sha256` | Hash of the exact serialized fragment used |
| `extracted_text_sha256` | Hash of normalized operative text |
| `parser_version` | Parser identity/version |
| `normalization_version` | Normalization rules identity/version |

Plus `import_run` key and date fields from §4A.

---

## 9. Security threat model (ZIP + XML)

| Threat | Mitigation |
|--------|------------|
| XXE / SSRF | Disable DTD/entity resolution and network in XML parsers |
| Entity expansion bombs | Entities off; max size/depth/elements |
| ZIP traversal | Reject `..` and absolute paths; sandboxed extract |
| ZIP bombs | Cap compressed + uncompressed bytes and file count |
| Untrusted XML as instructions | Data only; no LLM |
| Verified PDF rehost | Forbidden in fixture process |
| Terms/attribution drift | Pin Terms version on dataset |
| Huge Cap. 599-family ZIPs in git | Gitignore bulk; trim extracts only |
| RegLens trust-boundary collapse | Sibling paths only; no shared Pages/Studio |
| Path collision | `data/lawtrace/`, `fixtures/lawtrace/` — never RegLens `private-data/` for judgments |

---

## 10. Cap. 599-family census and showcase selection

Do **not** assume Cap. 599 principal ordinance is the best high-churn showcase.

**Census all `cap_599*` principal and subsidiary files** (current + past, English first):

| Measure | Use |
|---------|-----|
| File / version counts per instrument | Churn |
| Changed top-level sections between consecutive versions | Diff density |
| XML complexity (depth, table/img/form density) | Fidelity risk |
| Unsupported / potentially_lossy rates | Redline eligibility |

**Select showcase instrument only after census.** Then apply an explicit limiter (max versions × max sections) documented in the Stage D report.

Cap. 614 remains the primary contained parser fixture regardless of Cap. 599-family selection.

Config shape (not hard-coded architecture):

```yaml
spike_subjects:
  - cap: "614"
    role: primary_fixture
  - family: "599"
    role: stress_candidate
    select_after_census: true
```

---

## 11. XSD bundle

1. Acquire the **complete** official HKLM XSD bundle (entrypoint + all `import`/`include` targets).
2. Pin and SHA-256 hash every file; record bundle manifest.
3. Record **data-dictionary version/hash separately** from schema hash.
4. Validate fixtures **offline with network access disabled**.
5. Catalogue schema drift / validation failures by severity (`warn` vs `block`); **do not silently repair** invalid documents.

Published entrypoint checksum (to verify on acquisition):  
`4B0BA06E45F33BF97AC2C11CF9325764E8FCC92DE38E64FBD0ED8ED358DDB3BD` (138 KB, Version 1.0) — confirm against downloaded bundle.

---

## 12. Test-fixture strategy

1. Manual download from DATA.GOV.HK (documented curl/browser — **not** HKeL scrape): current/past ZIPs covering Cap. 614 and Cap. 599-family ranges; dictionary PDF; full XSD bundle.
2. Registry JSON: resource URL, download_datetime, Terms version, archive SHA-256, sizes.
3. Safe extract → trimmed `cap_614_*` + later selected Cap. 599-family extracts into `fixtures/lawtrace/`; bulk under `data/lawtrace/raw/` (gitignored).
4. Attribution file beside fixtures using mandatory legal-status wording.
5. Malicious ZIP/XXE fixtures for security tests (synthetic, tiny).

---

## 13. Execution staging (implementation after this plan only)

| Stage | Scope | Exit |
|-------|-------|------|
| **A** | Acquisition manifest, security utilities (safe ZIP/XML), corpus census (sizes, `cap_614*` + all `cap_599*`) | Manifest + census tables committed/reported |
| **B** | Cap. 614 parse; **top-level section** identity matrix; **date-semantics gate** | Report: date claim allowed or version-to-version fallback; identity metrics draft |
| **GATE** | **Human approval required** | No Stage C+ without written approval |
| **C** | Deterministic extraction, renderability classification, redline + reconstruction invariant | Diff proof + Cap. 614 full section-succession review |
| **D** | Selected Cap. 599-family stress test (≥30 stratified changed pairs if available) | Stress report + limiter |
| **E** | Final feasibility report vs §14 criteria | GO / GO WITH CONDITIONS / NO-GO |

**No product UI, no Pages, no Postgres into RegLens, no LLM.**

### Proposed Stage A file changes (exact; not created yet)

| Path | Purpose |
|------|---------|
| `docs/plans/lawtrace-feasibility-spike.md` | This plan (Stage 0 — **now**) |
| `fixtures/lawtrace/README.md` | Acquisition rules, attribution, legal-status wording |
| `fixtures/lawtrace/ATTRIBUTION.md` | Required attribution + Terms version pin |
| `fixtures/lawtrace/manifests/source_registry.jsonl` | Dataset/archive hashes, URLs, download_datetime, Terms version |
| `fixtures/lawtrace/manifests/corpus_census.json` | Cap. 614 + all `cap_599*` counts/sizes (post-download) |
| `fixtures/lawtrace/schema/hklm/` | Pinned XSD bundle + `BUNDLE_MANIFEST.json` (hashes) |
| `fixtures/lawtrace/schema/data-dictionary.meta.json` | Dictionary URL, version, SHA-256 |
| `data/lawtrace/raw/.gitkeep` + gitignore rules | Bulk ZIP storage (gitignored contents) |
| `services/lawtrace-worker/lawtrace_worker/security/zip_safe.py` | Path traversal + bomb guards |
| `services/lawtrace-worker/lawtrace_worker/security/xml_safe.py` | XXE-off, no-network parse helpers |
| `services/lawtrace-worker/lawtrace_worker/census.py` | Offline census over extracted/raw trees |
| `services/lawtrace-worker/pyproject.toml` or package stub | Sibling package scaffold (minimal) |
| `tests/lawtrace/test_zip_safe.py` | Traversal/bomb rejection |
| `tests/lawtrace/test_xml_safe.py` | XXE rejection |
| `tests/lawtrace/test_census_smoke.py` | Census runs on trimmed fixtures |

### Proposed Stage B file changes (exact; after Stage A; before human gate)

| Path | Purpose |
|------|---------|
| `fixtures/lawtrace/cap_614/**` | Trimmed Cap. 614 current/past English XML extracts |
| `fixtures/lawtrace/candidate_gold/cap_614_section_successions.provisional.jsonl` | Candidate/provisional succession edges (agent-reviewed; human_review_status=not_reviewed) |
| `services/lawtrace-worker/lawtrace_worker/parse_cap.py` | Instrument/section parse (top-level sections) |
| `services/lawtrace-worker/lawtrace_worker/identity.py` | Section identity + match_method |
| `services/lawtrace-worker/lawtrace_worker/date_semantics.py` | Field extraction + claim classification |
| `reports/lawtrace/stage_b_date_semantics.md` | Gate report: which date claims are supported |
| `reports/lawtrace/stage_b_identity_matrix.md` | `@id` stability + coverage/precision draft metrics |
| `tests/lawtrace/test_cap_614_parse.py` | Deterministic parse fixtures |
| `tests/lawtrace/test_date_semantics_labels.py` | Fields remain distinct; no silent merge |
| `tests/lawtrace/test_section_identity_scope.py` | Nested nodes lack independent identities |

Stages C–E file lists are deferred until Stage B human approval.

---

## 14. Measurable pass/fail criteria

**PASS:**

- Date-semantics gate documented; UI claim is either justified or explicitly version-to-version only.
- Cap. 614: 100% precision on automatically accepted **candidate/provisional** edges (agent-reviewed same run; not independent human gold); ≥95% coverage on ordinary same-section successions; uncertain → unmatched.
- Separate tallies for added/repealed/renumbered/substituted/split/consolidated/ambiguous.
- Provenance complete per §8; XPath never sole pointer.
- Renderability classified; no ordinary redlines for `potentially_lossy`/`unsupported`.
- Reconstruction invariant holds for published redlines.
- Cap. 599-family census complete; showcase selected with rationale; ≥30 stratified changed pairs reviewed if available.
- XSD bundle fully pinned; offline validation; drift catalogued (no silent repair).
- Mandatory legal-status wording present on any user-facing mock.
- Diff touches only LawTrace-namespaced paths; RegLens DO NOT TOUCH untouched; `make verify` green and uncoupled.

**FAIL (NO-GO):**

- Cannot define honest date semantics and still market “in force on date X” without evidence.
- Section `@id`/fallback matching fails precision or ordinary coverage gates.
- Forced text inference or sole-XPath provenance.
- Redlines published for unsupported/lossy content without detection.
- XSD bundle incomplete or requires network to validate.
- Coexistence lock violated (Pages/Studio/policy/migration coupling).

---

## 15. Rollback plan

- Removable LawTrace namespace only (`docs/plans/lawtrace-*`, `fixtures/lawtrace/`, `data/lawtrace/`, `services/lawtrace-worker/`, `tests/lawtrace/`, `reports/lawtrace/`).
- No RegLens schema/UI/policy/workflow changes.
- NO-GO → abandon fixtures; keep Stage E report as decision record.
- GO WITH CONDITIONS → separate product ADR; still no RegLens rewrite; still no shared Pages pipeline.

---

## 16. Three reduced-scope fallbacks

1. **Cap. 614 English-only section comparator** — drop Cap. 599-family stress test.
2. **Version-to-version only** — if date gate fails “in force” semantics (expected default until proven).
3. **Chapter-level diffs only** — if section identity precision cannot hit 100% on candidate/provisional accepted edges.

---

## 17. Answers to technical questions (pre-implementation)

1. **Architecture:** Sibling/namespaced; reuse hash/security patterns only — not RegLens domain.
2. **Identifiers:** Filename + doc meta; section `@id`/`@temporalId`/`num`; language; status; version datetime — with §4A distinctions.
3. **Stable IDs?** Claimed for `@id`; unverified until Stage B (sections only).
4. **Fallback:** `@temporalId` → unique section num → unmatched.
5. **Renumber/repeal/split:** Candidate classes + unmatched default; nested content not separately edged.
6. **XSD?** Offline full-bundle validation required (§11).
7. **Sizes?** Stage A measurement; Cap. 599-family census drives showcase choice.
8. **Normalization:** Versioned dual-channel rules (§7).
9. **Format vs text:** Renderability + dual channels; no generic drop of structured non-text.
10. **Unavailable:** Legal status; possibly effective/commencement; pre-1997; pending updates.
11. **Provenance:** §8 mandatory fields.
12. **Licensing unresolved:** Attribution string exactness; counsel; dictionary reprint limits.
13. **Spike failure:** Date dishonesty, identity precision failure, lossy silent redlines, incomplete XSD, coexistence breach.

---

## Deliverable status

| Item | Status |
|------|--------|
| This plan at `docs/plans/lawtrace-feasibility-spike.md` | **Written (Stage 0)** |
| Implementation Stages A–E | **Blocked until operators begin Stage A; Stage C+ blocked on human approval after B** |

# Core10 operations (RC4)

Core10 is an internal research-readiness loop before Core50 scale. It validates
source metadata, acquisition handling, extraction coverage, reviewer flow, and
reporting on a small set. It is **not** a public real-corpus release.

## Operating rule

GitHub Pages is publicly accessible. Real MCHK/DCHK corpus material, OCR text,
full page text, and reviewer notes remain in Studio/private storage unless a
future legal approval changes `source_publication_policy` and the release mode.

## Sequence

```text
metadata sync -> acquire -> extract -> review -> internal research
```

### 1. Metadata sync

Purpose: discover or refresh official index metadata without collecting raw
decision bodies in ordinary CI.

Commands:

```bash
make sources-status
make source-sync-mchk-dry
make source-sync-dchk-dry
```

Live metadata sync remains opt-in and requires:

- `REGLENS_MODE=postgres`;
- `DATABASE_URL`;
- source policy permitting the specific access mode;
- operator contact configured for the user agent;
- host/path allow-list and request budget.

If live contact is unset, do not run live sync.

### 2. Acquire

Purpose: place approved documents into internal storage for review.

Rules:

- Store real documents under gitignored `private-data/` or the configured object
  store only.
- Record provenance, source URL, acquisition timestamp, and SHA-256.
- Do not commit PDFs, HTML, OCR text, or page text.
- Do not copy acquired real documents into `apps/site/public/`,
  `generated/public-release`, or Pages artifacts.

### 3. Extract

Purpose: produce schema-valid propositions for review.

Rules:

- Deterministic parsing and evidence spans first.
- OCR text variants are internal only.
- Real-provider LLM processing requires separate privacy/runtime approval.
- Extracted propositions start pending/unpublished.
- Auto-accept remains limited to `--demo-auto-approve-synthetic`.

### 4. Review

Purpose: human reviewers accept, edit, reject, or mark uncertainty.

Checks:

- Every material proposition has supporting evidence.
- `epistemic_class` and `derivation` match the editorial handbook.
- Real-source caveats are preserved, including MCHK internal-only posture and the
  DCHK July 14, 2018 publication-coverage caveat.
- Uncertainty is recorded rather than hidden.

### 5. Internal research

Purpose: summarize readiness and qualitative findings for the project team.

Allowed outputs:

- Internal Core10 notes and reviewer observations.
- Synthetic/demo report artifacts from `make core10-report`.
- Human interpretation placeholders for future reviewer synthesis.

Not allowed:

- Publishing real Core10 decisions on Pages.
- Treating Core10 as a statistical sample.
- Describing synthetic report counts as real-world prevalence.
- Publicly releasing real excerpts while source policy remains `internal_only`.

## Synthetic report command

```bash
make core10-report
```

The report generator reads the reviewed synthetic demo release only, refuses
real/public-mode decisions, and writes labelled artifacts under `reports/core10/`.

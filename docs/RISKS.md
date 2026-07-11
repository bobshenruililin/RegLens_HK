# Risk register

## Milestone 2A (foundation)

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| L1 | Commercial use of MCHK text without consent | Critical | Internal-only; consent drafts only; policy `internal_only` |
| L4 | Invented citations | Critical | Span-mandatory evidence; no first-line fallback |
| T2 | LLM hallucination | Critical | Mock only; schema + domain validation |
| T2a | Non-deterministic extraction overwrites | High | Immutable run_key store + conflict quarantine |
| T2b | Auto-publication of model output | Critical | Default pending; demo flag synthetic-only |
| T2c | Real PDFs committed to Git | High | `fixtures/synthetic` + gitignored `private-data` + CI guard |
| T5 | Live scraping creep | High | Explicit exclusion; AGENTS.md |
| P1 | Patient PII in derived fields | High | Minimise derived fields; redaction + release scan |

## MVP-RC1 additions

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R1 | **Publication policy bypass** — shipping real judgments while sources are `internal_only`, or treating policy notes as optional | Critical | Release builder refuses `public` + `internal_only`; synthetic_demo cannot mix real fixtures; CI `check_public_release`; ADRs 0004–0005 |
| R2 | **Static hosting leakage** — Studio, secrets, raw objects, or API routes appear in Pages artifact | Critical | Separate `apps/site` with `output: "export"`; Pages workflow builds site only; guards forbid PDF/HTML and confidence; no Studio in artifact path |
| R3 | **Residual privacy** — redaction/scan miss patient or third-party identifiers in excerpts or claims | High | `redact_derived_text` + `scan_public_artifact`; excerpt caps; no claim of full de-identification; fail closed on known patterns |
| R4 | Corpus counts misread as prevalence | Medium | Methodology copy + EVALUATION note; global caveats in release manifest |
| R5 | Synthetic demo mistaken for real judgments | High | `release_mode=synthetic_demo` banners/caveats; attribution strings mark fixtures |
| R6 | Experimental 2B–2D features treated as production | Medium | Docs/MILESTONES mark experimental; Observatory does not depend on Postgres/FTS |
| R7 | Client-side search incompleteness or overclaim | Low | Document as catalog filter over published release only (ADR 0006) |

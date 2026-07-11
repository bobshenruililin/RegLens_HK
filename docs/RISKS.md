# Risk register (Milestone 2A update)

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| L1 | Commercial use of MCHK text without consent | Critical | Internal-only; consent drafts only |
| L4 | Invented citations | Critical | Span-mandatory evidence; no first-line fallback |
| T2 | LLM hallucination | Critical | Mock only; schema + domain validation |
| T2a | Non-deterministic extraction overwrites | High | Immutable run_key store + conflict quarantine |
| T2b | Auto-publication of model output | Critical | Default pending; demo flag synthetic-only |
| T2c | Real PDFs committed to Git | High | `fixtures/synthetic` + gitignored `private-data` + CI guard |
| T5 | Live scraping creep | High | Explicit exclusion; AGENTS.md |
| P1 | Patient PII in derived fields | High | Minimise derived fields; access control later |

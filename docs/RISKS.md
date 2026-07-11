# Legal, privacy and technical risk register

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| L1 | **Commercial use of MCHK text without consent** | Critical | Internal-only MVP; request written consent before public launch; short quotes only pending counsel |
| L2 | DCHK/NCHK licence ambiguity | High | Complete audit template; treat commercial use as consent-required |
| L3 | Product perceived as legal advice | High | UI disclaimers; no predictions; “research tool” framing |
| L4 | Misattribution / invented citations | Critical | Span-mandatory publish; quote alignment tests; never free-text authorities without evidence |
| L5 | Residual patient/third-party PII in PDFs | High | Do not surface raw full-text publicly; suppress obvious patient tokens in derived fields; access control |
| L6 | Defamation / unfair summary of practitioners | High | Prefer near-verbatim claims; human review; link to official source |
| L7 | Copyright withdrawal (MCHK may withdraw permission) | Medium | Takedown process; store licence snapshot date |
| P1 | PDPO: unnecessary personal data | High | Minimise derived fields; no DOB/address collection; purpose limitation |
| P2 | Sending judgments to third-party LLM | High | DPA; redact; or on-prem/VPC model; stub/mock in CI |
| T1 | OCR / segmentation errors break provenance | High | Confidence + coverage warnings; human review; text-first OCR fallback |
| T2 | LLM hallucination | Critical | Schema + quote match + review gate |
| T3 | Non-idempotent jobs duplicate data | Medium | `dedupe_key` = hash(pipeline, doc sha, prompt ver) |
| T4 | Prompt injection via malicious PDF text | Medium | Treat as data; no agent tools; sandbox |
| T5 | Scope creep to live scraping | High | Explicit exclusion; AGENTS.md; no scraper packages in MVP |

## Residual acceptance

Internal Milestone 1 demo on **synthetic** fixtures does not constitute a copyright licence for real judgments. Real fixture use remains under the internal-use posture documented in the audit.

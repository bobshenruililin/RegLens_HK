# Explicit MVP exclusions

- Live source adapters / scrapers / scheduled harvest
- NCHK (nurses) and any non-health regulator
- Chinese-first UI or bilingual aligned extraction
- Court of Appeal full-case integration beyond “appeal status as stated in judgment”
- Outcome prediction, sentencing guides, “similar case” recommendations that imply advice
- Public anonymous access and SEO-indexed full judgment republication
- Multi-tenant SaaS, billing, SSO beyond simple auth
- Real-time collaborative editing
- Mobile-native apps
- Automatic gazette cross-linking
- Graph visualisation of authorities (list + links to spans only)
- Microservices beyond `web` + `worker`

## Five ways to reduce scope further

1. **Drop semantic / pgvector** until keyword FTS proves insufficient (largest infra + eval savings).
2. **MCHK-only** for six weeks; add DCHK immediately after publish gate is proven.
3. **Extract only:** charges, rules, findings, sanctions, authorities — defer legal tests, costs, aggravating/mitigating.
4. **Skip OCR:** digital-text PDFs only; scanned docs marked `needs_ocr` and excluded from publish.
5. **Reviewer-CSV workflow** instead of full review UI: worker outputs JSON; reviewers edit; admin “publish” import — UI is search + decision page only.

## Challenges to requirements (unnecessary or unsafe)

| Requirement | Challenge | Recommendation |
|-------------|-----------|----------------|
| Three professions (doctors, dentists, **nurses**) with **two** bodies | Internally inconsistent; NCHK corpus/licensing differs | **Two bodies = MCHK + DCHK**; nurses later |
| Semantic search in MVP | High cost, weak eval signal early; risk of “similar cases” being read as advice | Ship FTS first; semantic behind flag or cut (§1 above) |
| Always OCR + page spans | Unnecessary for text-layer PDFs; OCR introduces false provenance | Text-first; OCR fallback only |
| Extract **legal tests** | Highly interpretive; blurs fact/interpretation; hallucination magnet | Keep only as `interpretation`, review-mandatory — or defer (§3) |
| Full decision republication in UI | Conflicts with MCHK commercial-use copyright limits | Short cited quotes + link to official URL; full text only for licensed/internal roles |
| Early multi-regulator “platform” abstraction | Premature generality | Two hard-coded source profiles; shared schema |
| Patient-name scrubbing as guarantee | Sources may still embed PII; perfect scrubbing is false security | Access control + minimise derived fields + warn; do not claim de-identification |

# Threat model (MVP-RC2) — concise

Scope: Studio + worker + Postgres + object store + RC3 source sync/OCR/LLM
gates + Observatory static host.
Not a formal STRIDE spreadsheet.

## Assets

- Raw judgment bytes (synthetic fixtures; real under gitignored `private-data/`)
- Extraction runs, pending propositions, review notes
- Studio credentials / sessions
- Approved publication bundles (public)

## Trust boundaries

```text
private-data / object store / Postgres ──► Studio + worker (authenticated)
                    │
                    ▼ publication transaction + privacy scan
         generated/public-release* ──► apps/site ──► GitHub Pages
```

Crossing the publication boundary without `release build` /
`build_release_from_postgres` + public-scan is a defect.

## Key threats and mitigations

| Threat | Mitigation |
|--------|------------|
| Real docs in git / Pages | gitignore `private-data/`; fixture check; public-scan; Studio off Pages |
| Accidental real public release | Policy `internal_only`; `public` mode refuses synthetic + internal sources |
| Demo auto-approve on real data | Flags/pipeline reject non-synthetic |
| Remote DB wipe | `assert_local_database_url` on `db-reset-local` |
| Session theft | Hashed tokens; fail-closed production secrets; no secrets in site export |
| Prompt injection via documents | Treat docs as data; mock LLM only until privacy approval |
| Source overreach | Policy-aware sync; offline CI fixtures; manual source-health; no PDF downloads |
| Licence confusion | Public availability is not reuse permission; robots.txt is not a licence |
| Privacy overclaim | Privacy scan required, but no complete de-identification claim |
| Mixed synthetic/real release | Validate fail-closed; no mixed corpus |
| Schema drift / silent migrate | Checksummed `schema_migrations` |

## Out of scope (current)

Broad live crawling, public real releases, real LLM providers without runtime
approval, semantic search, NCHK, outcome prediction, multi-tenant SaaS isolation.
MCHK remains internal-only; DCHK outputs must carry the July 14, 2018 caveat;
student-research letters do not unlock Pages.

## Related

- [`../SECURITY.md`](../SECURITY.md)
- [`adr/0003-synthetic-private-data-boundary.md`](adr/0003-synthetic-private-data-boundary.md)
- [`adr/0010-explicit-storage-modes.md`](adr/0010-explicit-storage-modes.md)
- [`SOURCE_SYNC.md`](SOURCE_SYNC.md)
- [`CRAWL_POLICY.md`](CRAWL_POLICY.md)

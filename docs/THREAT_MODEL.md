# Threat model (MVP-RC2) — concise

Scope: Studio + worker + Postgres + object store + Observatory static host.
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
| Mixed synthetic/real release | Validate fail-closed; no mixed corpus |
| Schema drift / silent migrate | Checksummed `schema_migrations` |

## Out of scope (current)

Live crawl, OCR, real LLM providers, semantic search, NCHK, outcome prediction,
multi-tenant SaaS isolation.

## Related

- [`../SECURITY.md`](../SECURITY.md)
- [`adr/0003-synthetic-private-data-boundary.md`](adr/0003-synthetic-private-data-boundary.md)
- [`adr/0010-explicit-storage-modes.md`](adr/0010-explicit-storage-modes.md)

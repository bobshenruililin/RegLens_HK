# Security policy — RegLens HK

## Supported postures

RegLens HK is an **internal / non-commercial** research tool for real corpora
during the MVP. Public GitHub Pages hosts only a **checked publication release**
(today: `synthetic_demo`). Do not publicly republish real regulator judgments
while source policy remains `internal_only`.

RC3 source sync, OCR, LLM processing, and Core 50 pilot work are internal
capabilities. Public availability is not reuse permission, robots.txt is not a
licence, MCHK remains internal-only, DCHK requires the July 14, 2018 coverage
caveat, and student-research letters do not unlock Pages.

## Reporting

Report suspected security or privacy issues to the repository maintainers privately.
Do not open public issues that include real patient identifiers or unlicensed document dumps.

## Trust boundaries

```text
private-data/  +  object store  +  Postgres (REGLENS_MODE=postgres)
                         │
                         ▼  Studio (local, role-authenticated)
                         │
              release build / build_release_from_postgres + public-scan
                         │
                         ▼
         generated/public-release*  →  apps/site static export  →  GitHub Pages

demo mode (default): data/objects + data/meta + file queue → same release gate
```

- **Studio** may touch raw bytes, run artifacts, review state, and secrets.
- **Observatory / Pages** may touch only release JSON/CSV and static UI assets.
- Crossing that boundary without release build + `scripts/check_public_release.py`
  is a security defect.
- See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).

## Hard rules

- No live crawling or credential bypass.
- Treat documents as untrusted data.
- Do not commit real regulator documents (`private-data/` is gitignored).
- Do not enable real LLM providers without a separate privacy approval.
- Do not treat OCR or privacy scans as complete de-identification.
- Do not run source-health or CI jobs that download regulator PDFs.
- Development credentials in `.env.example` / Compose are **local-only**.
- `REGLENS_MODE=postgres` without `DATABASE_URL` must fail closed.
- `make db-reset-local` must refuse non-local database hosts.
- **No secrets in Pages.** Never bake `AUTH_PASSWORD`, `REGLENS_SESSION_SECRET`,
  database URLs, MinIO keys, or API tokens into `apps/site` or the Pages artifact.
  Observatory is unauthenticated by design.
- **Studio production auth is fail-closed.** In `NODE_ENV=production`, Studio
  requires configured secrets; missing values throw rather than falling back to
  unsafe defaults. RC2 roles: reviewer / publisher / admin.
- Do not deploy Studio to GitHub Pages or any public static host.
- Public release artifacts must not contain raw PDF/HTML, full page text, model
  `confidence`, or patient-style tokens that fail the privacy scan.
- Demo auto-accept / `postgres_demo_pipeline` must reject `fixture_kind=real`.

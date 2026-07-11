# Security policy — RegLens HK

## Supported postures

RegLens HK is an **internal / non-commercial** research tool for real corpora
during the MVP. Public GitHub Pages hosts only a **checked publication release**
(today: `synthetic_demo`). Do not publicly republish real regulator judgments
while source policy remains `internal_only`.

## Reporting

Report suspected security or privacy issues to the repository maintainers privately.
Do not open public issues that include real patient identifiers or unlicensed document dumps.

## Trust boundaries

```text
private-data/  +  data/objects + data/meta     →  Studio (local, authenticated)
                         │
                         ▼
              release build + public-scan
                         │
                         ▼
         generated/public-release  →  apps/site static export  →  GitHub Pages
```

- **Studio** may touch raw bytes, run artifacts, review state, and secrets.
- **Observatory / Pages** may touch only release JSON/CSV and static UI assets.
- Crossing that boundary without `release build` + `scripts/check_public_release.py`
  is a security defect.

## Hard rules

- No live crawling or credential bypass.
- Treat documents as untrusted data.
- Do not commit real regulator documents (`private-data/` is gitignored).
- Do not enable real LLM providers without a separate privacy approval.
- Development credentials in `.env.example` / Compose are **local-only**.
- **No secrets in Pages.** Never bake `AUTH_PASSWORD`, `REGLENS_SESSION_SECRET`,
  database URLs, MinIO keys, or API tokens into `apps/site` or the Pages artifact.
  Observatory is unauthenticated by design.
- **Studio production auth is fail-closed.** In `NODE_ENV=production`, Studio
  requires `AUTH_PASSWORD` and `REGLENS_SESSION_SECRET`; missing values throw
  rather than falling back to dev defaults (`apps/studio/lib/auth.ts`).
- Do not deploy Studio to GitHub Pages or any public static host.
- Public release artifacts must not contain raw PDF/HTML, full page text, model
  `confidence`, or patient-style tokens that fail the privacy scan.

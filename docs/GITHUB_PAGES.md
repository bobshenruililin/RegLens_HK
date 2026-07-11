# GitHub Pages — RegLens Observatory

Observatory is deployed as a **static** site from `apps/site/out`. Studio is
never part of the Pages artifact.

## What Pages may contain

- Static HTML/CSS/JS from the Next.js export
- Checked publication release files under `/data/release/` (JSON/CSV/checksums)
- Public UI copy and methodology text

## What Pages must not contain

- `apps/studio` build output
- Raw judgment PDF/HTML or `private-data/`
- Full page-text arrays, model `confidence`, extractor metadata
- Secrets (`AUTH_PASSWORD`, `REGLENS_SESSION_SECRET`, DB/MinIO credentials)
- Next.js API routes or middleware (export guards assert their absence)

## Workflow

[`.github/workflows/pages.yml`](../.github/workflows/pages.yml):

1. Install Python + Node 20
2. Fixture guards + `make pages-artifact` (demo release → site `public/data/release`)
3. `check_public_release.py` + additional raw-file / confidence / patient-token scans
4. `apps/site` `npm ci` / typecheck / build (`NEXT_PUBLIC_BASE_PATH` from repo variable)
5. Verify static routes and decision pages; assert no `out/api` or middleware
6. `actions/upload-pages-artifact` on `apps/site/out`
7. `actions/deploy-pages`

Triggers: push to `main`, and `workflow_dispatch`.

## Manual enablement steps (repository admin)

GitHub Actions cannot fully enable Pages on a fresh repo without a one-time
human configuration:

1. Open the repository on GitHub → **Settings** → **Pages**.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**
   (not “Deploy from a branch”).
3. Ensure Actions are allowed for the repository (Settings → Actions → General).
4. Confirm the `GitHub Pages` environment exists (created automatically on first
   successful `deploy-pages` run, or create **Settings → Environments →
   github-pages**).
5. Optional: set repository variable **`PAGES_BASE_PATH`** if the site is served
   from a project-pages subpath (e.g. `/RegLens_HK`). Leave empty for a custom
   domain or user/org root site.
6. Push to `main` or run **Actions → GitHub Pages → Run workflow**.
7. After the deploy job succeeds, copy the environment URL from the workflow
   summary / Pages settings. First enablement may require approving the
   `github-pages` environment if protection rules are configured.
8. Verify: home, explore, analytics, methodology, data, compare, a decision
   slug, and that no PDF judgment files are reachable under `/data/release/`.

If the workflow is skipped or the deploy job waits on approval, check environment
protection rules and that the acting actor has rights to approve.

## Local parity

```bash
make site-build
# inspect apps/site/out
```

`make verify` includes `site-ci`, which depends on `pages-artifact`.

## Failure policy

Any public-scan failure, presence of raw sources, or missing static routes must
fail the build. Do not “deploy anyway” with an unchecked `data/` tree.

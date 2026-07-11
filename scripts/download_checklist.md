# Manual fixture acquisition checklist

RegLens HK does **not** ship crawlers. Operators download documents manually.

1. Confirm the source row in `docs/SOURCE_LICENSING_AUDIT.md` has `mvp_allowed=true` for internal use.
2. Open the official index URL in a normal browser session.
3. Download the PDF/HTML using the browser’s save function.
4. Place the file under `fixtures/raw/{mchk|dchk}/`.
5. Append a JSONL row to `fixtures/manifests/` with:
   - `regulator_code`, `source_id`, `relative_path`
   - `external_ref`, `title`, `source_url`, `downloaded_at`
   - `notes` (include “manual download”)
6. Run `python -m reglens_worker hash <file>` and record the SHA-256 in operator notes if required.
7. Run ingest: `python -m reglens_worker ingest --manifest fixtures/manifests/<file>.jsonl`
8. Never commit credentials, authenticated cookies, or scraped bulk archives.

Synthetic fixtures already in-tree are labelled **SYNTHETIC FIXTURE** and are not official judgments.

# Manual fixture acquisition checklist

RegLens HK does **not** ship crawlers.

## Synthetic (tracked)

Use `fixtures/synthetic/` and `fixtures/manifests/*.jsonl` with `"fixture_kind":"synthetic"`.

## Real documents (never commit)

1. Confirm licensing audit row allows internal use (`docs/SOURCE_LICENSING_AUDIT.md`).
2. Manually download via browser Save As.
3. Store under `private-data/raw/{mchk|dchk}/` (gitignored).
4. Append a JSONL row under `private-data/manifests/` with `"fixture_kind":"real"`.
5. Hash with `python -m reglens_worker hash <file>`.
6. Ingest pointing fixtures root appropriately — **never** pass `--demo-auto-approve-synthetic`.

Do not commit credentials, cookies, or real PDFs.

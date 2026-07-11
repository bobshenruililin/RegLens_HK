# Private-data layout (not tracked)

Real, manually acquired regulator documents **must not** be committed to Git.

Place them outside the tracked tree as follows (created locally; gitignored):

```text
private-data/
  README.md                 # optional local notes (gitignored with tree)
  raw/
    mchk/                   # manually downloaded MCHK PDFs/HTML
    dchk/                   # manually downloaded DCHK PDFs/HTML
  manifests/
    local.jsonl             # fixture_kind=real rows; never commit
```

Manifest rows for real documents must set `"fixture_kind": "real"`.

Acquisition remains manual only — see `scripts/download_checklist.md`.
Do not scrape. Do not use `--demo-auto-approve-synthetic` on real rows
(the flag rejects non-synthetic manifests).

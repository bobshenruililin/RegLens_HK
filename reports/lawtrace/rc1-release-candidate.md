# LawTrace HK Website Release Candidate 1

## Result: **PASS WITH LIMITATIONS**

## Preview

No public deployment. Local production preview:

```bash
make lawtrace-preview
# → http://127.0.0.1:3010/

# Cap. 599G complete local-real:
make lawtrace-preview-local
```

Optional local review workspace (not auth): `LAWTRACE_LOCAL_REVIEW=1 make lawtrace-build-local`

## Dataset coverage

| Instrument | Mode | Coverage |
|------------|------|----------|
| Cap. 614 | Demo (committed) | 12/12 complete; recon 392/392 |
| Cap. 599G | Local-real | **101/101 complete**; recon 3401/3401; ~52MB web data; build ~484 pages |

## Artifact / build timings (this environment)

- Cap. 599G full export: ~30s
- Local static build (614+599G): ~16s, out ~96MB
- Demo `make lawtrace-ci`: ~20s
- `make verify`: ~44s (150 passed, 2 skipped)

## Screenshots

Committed under `docs/assets/lawtrace/`:

1. landing
2. Cap. 614 instrument
3. Cap. 599G instrument
4. transition
5–6. comparator
7. section history
8. insights
9. methodology
10. mobile comparator

## CI

Dedicated workflow: `.github/workflows/lawtrace.yml`

## Explicit prohibitions honored

- No public launch
- No LLM explanation layer

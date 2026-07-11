# RegLens HK

Evidence-linked database for Hong Kong regulatory disciplinary decisions
(MCHK and DCHK). Not legal advice. Not outcome prediction.

**MVP-RC1** ships two deliberately separated surfaces:

| Surface | Path | Audience | Hosting |
|---------|------|----------|---------|
| **RegLens Studio** | `apps/studio` | Internal reviewers / operators | Local only — never GitHub Pages |
| **RegLens Observatory** | `apps/site` | Public, read-only research site | Static export → GitHub Pages |

Studio holds raw artifacts, review queues, and experimental auth. Observatory
consumes only a **versioned, privacy-checked publication release** under
`generated/public-release` (copied into `apps/site/public/data/release` for
static build). Pages deploys **must not** include Studio, raw PDFs/HTML, model
confidence, or full page text.

## Product posture (read carefully)

- **Synthetic technical MVP** (current default): `release_mode=synthetic_demo`
  with fixtures under `fixtures/synthetic/`. Demonstrates pipeline and public UX.
- **Real research pilot**: real documents live only under gitignored
  `private-data/`; Studio-internal use. A real **`public` release is blocked**
  while `source_publication_policy` marks MCHK/DCHK as `internal_only`.
- The public site is **not** an authenticated research environment.
- Counts and charts on Observatory describe the **published corpus** in that
  release — not population prevalence or regulator-wide rates.
- GitHub Pages contains **no raw documents**.

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/worker/requirements.txt
export PYTHONPATH=services/worker

# Synthetic ingest (auto-approve synthetic rows only)
make demo-ingest

# Build privacy-checked synthetic_demo release + validate
make demo-release

# Internal Studio (local)
make studio-dev

# Public Observatory (local; needs pages-artifact / demo-release data)
make site-dev

# Full verification gate
make verify
```

| Target | Purpose |
|--------|---------|
| `make demo-ingest` | Wipe `data/`, ingest `fixtures/manifests/m1.jsonl` with `--demo-auto-approve-synthetic` |
| `make demo-release` | Ingest + build `generated/public-release` + `scripts/check_public_release.py` |
| `make studio-dev` | Next.js Studio on localhost |
| `make site-dev` | Next.js Observatory on localhost |
| `make pages-artifact` | Copy release into `apps/site/public/data/release` for static export |
| `make verify` | Fixtures, lint, types, pytest, Studio CI, demo-release, public-scan, site CI |

## Documentation

Full index: **[docs/README.md](docs/README.md)**

| Topic | Doc |
|-------|-----|
| Architecture (Studio vs Observatory) | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Observatory product | [docs/OBSERVATORY.md](docs/OBSERVATORY.md) |
| Publication releases | [docs/PUBLICATION_RELEASES.md](docs/PUBLICATION_RELEASES.md) |
| GitHub Pages enablement | [docs/GITHUB_PAGES.md](docs/GITHUB_PAGES.md) |
| Agent / trust-boundary rules | [AGENTS.md](AGENTS.md) |
| Security | [SECURITY.md](SECURITY.md) |
| Local setup | [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md) |

## Licence

See [LICENSE](LICENSE). Source republication remains constrained by each
regulator’s copyright notice and by
[`publications/policies/source_publication_policy.v1.json`](publications/policies/source_publication_policy.v1.json).

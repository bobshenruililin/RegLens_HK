# RegLens HK

Evidence-linked database for Hong Kong regulatory disciplinary decisions
(MCHK and DCHK). Not legal advice. Not outcome prediction.

**MVP-RC1** shipped Observatory + publication releases. **MVP-RC2** adds a
trusted Studio data plane (`REGLENS_MODE=demo|postgres`) while keeping the
public site on checked static bundles only. **MVP-RC3** adds policy-aware
source-sync, OCR/LLM gates, and an internal Core 50 pilot; it does **not** add a
public real-corpus release. **MVP-RC4** adds public synthetic-only Observatory
enrichment pages and Core10 internal research/report tooling before Core50
scale.

| Surface | Path | Audience | Hosting |
|---------|------|----------|---------|
| **RegLens Studio** | `apps/studio` | Internal reviewers / operators | Local only — never GitHub Pages |
| **RegLens Observatory** | `apps/site` | Public, read-only research site | Static export → GitHub Pages |

Studio holds raw artifacts, review queues, and auth. Observatory consumes only a
**versioned, privacy-checked publication release** under
`generated/public-release` (or `generated/public-release-pg` from the Postgres
demo pipeline). Pages deploys **must not** include Studio, raw PDFs/HTML, model
confidence, or full page text.

## Product posture (read carefully)

- **Synthetic technical MVP** (current default): `release_mode=synthetic_demo`
  with fixtures under `fixtures/synthetic/`. Demonstrates pipeline and public UX.
- **Real research pilot**: real documents live only under gitignored
  `private-data/` or private object storage; Studio-internal use. A real
  **`public` release is blocked** while `source_publication_policy` marks
  MCHK/DCHK as `internal_only`.
- **RC3 source posture**: public availability is not reuse permission; robots.txt
  is not a licence. MCHK remains internal-only, DCHK carries the July 14, 2018
  publication caveat, and student-research letters do not unlock Pages.
- GitHub Pages is publicly accessible. The public site is **not** an
  authenticated research environment.
- Counts and charts on Observatory describe the **published corpus** in that
  release — not population prevalence or regulator-wide rates.
- GitHub Pages contains **no raw documents**.
- Privacy scans reduce risk but are not a claim of complete de-identification.

## Quick start (demo mode — no DATABASE_URL)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r services/worker/requirements.txt
export PYTHONPATH=services/worker

make demo-ingest
make demo-release
make studio-dev          # internal
make site-dev            # Observatory (needs pages-artifact / demo-release)
make verify              # RC2 demo-mode gate
```

| Target | Purpose |
|--------|---------|
| `make demo-ingest` / `demo-enqueue` / `worker-once` | Synthetic filesystem pipeline |
| `make demo-release` | Build + scan `generated/public-release` |
| `make verify` | Fixtures, lint, types, pytest, Studio/site CI, demo-release |
| `make rc3-verify` | Focused RC3 source/OCR/LLM/pipeline tests and ruff |
| `make core10-report` / `rc4-verify` | Synthetic-only Core10 report + RC4 verification |
| `make sources-status` / `source-sync-*-dry` | Source policy status and offline fixture sync |
| `make core50-status` / `extraction-eval` | Internal pilot and synthetic eval pointers |
| `make db-up` + `db-migrate` | Local Postgres 16 (RC2; migrate required) |
| `make postgres-demo-pipeline` | Synthetic-only Postgres demo → `public-release-pg` |
| `make integration` | Postgres tests (skips locally without DSN; fails in CI if unset) |

## Documentation

Full index: **[docs/README.md](docs/README.md)**

| Topic | Doc |
|-------|-----|
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Product positioning | [docs/PRODUCT_POSITIONING.md](docs/PRODUCT_POSITIONING.md) |
| Studio | [docs/STUDIO.md](docs/STUDIO.md) |
| Operations / migrations | [docs/OPERATIONS.md](docs/OPERATIONS.md), [docs/DATABASE_MIGRATIONS.md](docs/DATABASE_MIGRATIONS.md) |
| Observatory | [docs/OBSERVATORY.md](docs/OBSERVATORY.md) |
| Publication releases | [docs/PUBLICATION_RELEASES.md](docs/PUBLICATION_RELEASES.md) |
| Editorial / Core10 research | [docs/EDITORIAL_HANDBOOK.md](docs/EDITORIAL_HANDBOOK.md), [docs/CORE10_OPERATIONS.md](docs/CORE10_OPERATIONS.md), [docs/RESEARCH_COLLECTIONS.md](docs/RESEARCH_COLLECTIONS.md) |
| User research | [docs/USER_RESEARCH.md](docs/USER_RESEARCH.md) |
| RC3 source sync / crawl policy | [docs/SOURCE_SYNC.md](docs/SOURCE_SYNC.md), [docs/CRAWL_POLICY.md](docs/CRAWL_POLICY.md) |
| RC3 pilot / OCR / LLM | [docs/REAL_CORPUS_PILOT.md](docs/REAL_CORPUS_PILOT.md), [docs/OCR.md](docs/OCR.md), [docs/LLM_PROCESSING.md](docs/LLM_PROCESSING.md) |
| Agent rules | [AGENTS.md](AGENTS.md) |
| Security / threat model | [SECURITY.md](SECURITY.md), [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md) |
| Local setup | [docs/LOCAL_SETUP.md](docs/LOCAL_SETUP.md) |

## Licence

See [LICENSE](LICENSE). Source republication remains constrained by each
regulator’s copyright notice, consent posture, and by
[`publications/policies/source_publication_policy.v1.json`](publications/policies/source_publication_policy.v1.json).
robots.txt does not change those constraints.

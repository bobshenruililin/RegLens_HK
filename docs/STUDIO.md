# Studio operator guide (MVP-RC2 / RC4)

RegLens Studio (`apps/studio`) is the **internal** review and operations UI.
It never deploys to GitHub Pages. Observatory (`apps/site`) remains a separate
static consumer of checked publication releases.

## Modes

| `REGLENS_MODE` | Studio data plane | When to use |
|----------------|-------------------|-------------|
| `demo` (default) | Local `data/` seed + file job queue | Offline synthetic demos; `make verify` |
| `postgres` | PostgreSQL + object store | RC2 trusted path; requires `DATABASE_URL` |

Fail-closed: `REGLENS_MODE=postgres` without `DATABASE_URL` refuses to start.

## Local Studio (demo)

```bash
make demo-ingest   # or demo-enqueue + worker-once
make studio-dev
```

Production Studio auth is fail-closed (`AUTH_PASSWORD`, `REGLENS_SESSION_SECRET`
when `NODE_ENV=production`). See [`adr/0012-studio-auth-role-model.md`](adr/0012-studio-auth-role-model.md).

## Local Studio (postgres)

```bash
make db-up
export DATABASE_URL=postgresql://reglens:reglens_local_only@127.0.0.1:5432/reglens
export REGLENS_MODE=postgres
make db-migrate
make demo-enqueue
make worker-once
make studio-dev
```

Create an admin user via the demo pipeline or `reglens_worker.pg.users.create_user`
(roles: `reviewer`, `publisher`, `admin`).

## Trust boundary

- Studio may read raw blobs, extraction runs, pending propositions, and audit events.
- Public Observatory may only see bundles from `release build` /
  `build_release_from_postgres` after `scripts/check_public_release.py`.
- Do not point Studio at a public host or bake secrets into `apps/site`.

## RC3 source and pilot posture

Studio is the internal surface for RC3 source metadata, OCR text variants,
bounded extractor/critic output, corrections, and Core 50 pilot review. These
features do not authorize public real releases. Public availability is not reuse
permission; robots.txt is not a licence; MCHK remains internal-only; DCHK records
need the July 14, 2018 caveat; privacy scans are not complete de-identification;
and student-research letters do not unlock Pages.

## RC4 Core10 posture

Core10 is the internal readiness loop before Core50 scale:

1. metadata sync;
2. acquire;
3. extract;
4. review;
5. internal research.

Real Core10 materials stay in Studio/private storage. GitHub Pages is publicly
accessible and may only show synthetic/demo release data plus explanatory
synthetic pages. Use [`CORE10_OPERATIONS.md`](CORE10_OPERATIONS.md) for operator
steps and [`EDITORIAL_HANDBOOK.md`](EDITORIAL_HANDBOOK.md) for coding guidance.

## Related

- [`OPERATIONS.md`](OPERATIONS.md) — Compose, workers, backups
- [`REVIEW_WORKFLOW.md`](REVIEW_WORKFLOW.md) — accept / edit / reject / publish
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — two-app overview
- [`SOURCE_SYNC.md`](SOURCE_SYNC.md) — RC3 source sync
- [`CORE10_OPERATIONS.md`](CORE10_OPERATIONS.md) — Core10 internal sequence
- [`EDITORIAL_HANDBOOK.md`](EDITORIAL_HANDBOOK.md) — editorial codebook
- [`REAL_CORPUS_PILOT.md`](REAL_CORPUS_PILOT.md) — Core 50 internal pilot

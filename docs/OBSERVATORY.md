# RegLens Observatory (MVP-RC1)

Observatory is the **public, read-only** research website for RegLens HK. It is
implemented in `apps/site` as a Next.js static export and is the only frontend
eligible for GitHub Pages.

## What it is

- A corpus browser over a **versioned publication release**
  (`apps/site/public/data/release/`, produced by `make pages-artifact`).
- Unauthenticated. No review queue, no operator APIs, no session cookies.
- Explicitly **not** an authenticated research environment (that role is Studio).

## What it is not

- Not a republication of full judgments.
- Not Studio (`apps/studio`) under another name.
- Not a prevalence dashboard for all Hong Kong disciplinary outcomes.
- Not a channel for raw PDFs/HTML or `private-data/`.

## Synthetic technical MVP vs real research pilot

| Mode | Observatory content |
|------|---------------------|
| `synthetic_demo` (current Pages default) | Synthetic fixtures only; labelled as demo; safe engineering MVP |
| `public` | Real reviewed decisions **only if** each source policy allows (today: blocked — MCHK/DCHK are `internal_only`) |

A real research pilot using manually acquired judgments remains **Studio-internal**
until consent/licence posture and `source_publication_policy` change together.

## Routes (static)

| Route | Purpose |
|-------|---------|
| `/` | Landing + corpus posture caveats |
| `/explore/` | Client-side filter over `catalog.json` |
| `/decisions/[slug]/` | Public decision page (excerpts + taxonomy + takeaway) |
| `/analytics/` | Charts/tables for **this release’s** corpus |
| `/methodology/` | How extracts and releases are produced |
| `/data/` | Release manifest, checksums, downloadable CSV/JSON pointers |
| `/compare/` | Side-by-side comparison within the published set |
| `/404` | Static not-found |

## Data contract

Observatory loads only release artifacts (see [`PUBLICATION_RELEASES.md`](PUBLICATION_RELEASES.md)):

- `release.json` — identity, mode, caveats, counts
- `catalog.json` — list/filter index
- `analytics.json` — aggregates for charts
- `decisions/*.json` — `public_decision.v1` records
- `checksums.sha256` — integrity

Build-time loaders live in `apps/site/lib/release.ts`. Client explore uses the
same JSON after static copy into `public/`.

## Trust rules

1. Pages artifact path is `apps/site/out` only (see [`GITHUB_PAGES.md`](GITHUB_PAGES.md)).
2. No Studio middleware, `/api`, or env secrets in the export.
3. Counts describe the **published corpus**; methodology and UI must say so.
4. Global and per-decision caveats from the release must remain visible.
5. GitHub Pages contains **no raw documents**.

## Local run

```bash
make demo-release
make pages-artifact
make site-dev
```

Full gate: `make verify`.

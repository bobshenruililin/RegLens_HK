# ADR 0004 — Studio / Observatory separation

## Status

Accepted (MVP-RC1)

## Context

Milestone 2A shipped a single Next.js app (`apps/web`) that mixed decision
review, local artifact access, and (experimental) authentication. That app
cannot be statically exported safely for GitHub Pages: it expects server
routes, cookies, and privileged data paths. A public research site needs a
different trust model.

## Decision

Split frontends:

1. **`apps/studio` (RegLens Studio)** — internal operator UI. May use auth,
   review APIs, and local `data/` artifacts. **Must not** be deployed to GitHub
   Pages or any public static host.
2. **`apps/site` (RegLens Observatory)** — public read-only UI. `output: "export"`,
   no API routes, no session secrets. Consumes only a checked publication
   release under `public/data/release/`.

Pages workflows upload `apps/site/out` only.

## Consequences

- Contributors maintain two package trees and two CI targets (`studio-ci`,
  `site-ci`).
- Public UX cannot silently gain Studio capabilities.
- Real research pilots stay in Studio until a policy-compliant release exists.
- Documentation and AGENTS.md treat cross-deploying Studio as a security defect.

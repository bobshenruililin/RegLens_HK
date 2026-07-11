# ADR 0006 — Static client search on Observatory

## Status

Accepted (MVP-RC1)

## Context

Product requirements historically called for Postgres FTS (and later semantic
search) over published propositions. Those capabilities need a server, index
updates, and authenticated operator assumptions. GitHub Pages hosting for
Observatory forbids a search backend. Experimental Studio search (Milestone 2D)
is not production FTS and must not be exposed publicly.

## Decision

Observatory **explore** uses **client-side filtering** over the static
`catalog.json` (and related release JSON) shipped with the site. No query API,
no Postgres, no pgvector on Pages.

Studio may retain experimental keyword/substring search against local seed data
for operators; that path is out of scope for Pages and is not the public
contract.

## Consequences

- Public search quality is bounded by catalog fields and browser-side filters.
- Corpus size for Pages must remain appropriate for static JSON download.
- Evaluation of Observatory explore is UX/corpus navigation, not retrieval
  benchmarking against a full regulator collection
  (see [`EVALUATION.md`](../EVALUATION.md) §8).
- Adding server search later requires a non-Pages hosting decision and a new ADR.

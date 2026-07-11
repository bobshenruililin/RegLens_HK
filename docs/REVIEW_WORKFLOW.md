# Review workflow (MVP-RC2)

Human review is mandatory for production publication. Model output defaults to
**pending** / unpublished.

## Roles

| Role | Typical actions |
|------|-----------------|
| `reviewer` | Accept, edit, reject proposition revisions |
| `publisher` | Draft / validate / approve publication releases |
| `admin` | User admin + all of the above |

See [`adr/0012-studio-auth-role-model.md`](adr/0012-studio-auth-role-model.md).

## Proposition path

1. Ingest creates immutable `extracted_propositions` + revision 1 + pending `reviews`.
2. Reviewer **accepts** the head revision, **edits** (append-only new revision),
   or **rejects**.
3. Only `accepted` / `edited` heads with ≥1 evidence span are publishable.
4. Editorial annotations (taxonomy categories + summary/takeaway) are required
   before release approve.

Optimistic concurrency: review/edit APIs take `expected_head_revision_number`
and fail closed on conflict ([`adr/0009-immutable-proposition-revisions.md`](adr/0009-immutable-proposition-revisions.md)).

## Demo-only auto-accept

- Filesystem: `--demo-auto-approve-synthetic` / `make demo-ingest` — synthetic
  rows only; rejects real fixtures.
- Postgres demo: `scripts/postgres_demo_pipeline.py` labels review notes
  **DEMO ONLY** and refuses `fixture_kind=real`.

Neither path is a production review substitute.

## Publication

1. Create draft release (`synthetic_demo` or `public`).
2. Attach included decisions.
3. `validate_release` / `approve_and_build_release` (fail closed).
4. Compile `publication_release.v1` via filesystem `release build` or
   `build_release_from_postgres`.
5. `scripts/check_public_release.py` before Observatory/Pages.

See [`adr/0011-publication-transaction.md`](adr/0011-publication-transaction.md)
and [`PUBLICATION_RELEASES.md`](PUBLICATION_RELEASES.md).

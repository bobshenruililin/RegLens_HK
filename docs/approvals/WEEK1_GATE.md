# Week 1 implementation gate

| Field | Value |
|-------|-------|
| Gate | Begin Week 1 only after Phase 0 docs approval + licence posture confirmed |
| Phase 0 docs | Approved — see `PHASE0_APPROVAL.md` and `docs/README.md` |
| Licence posture | **Confirmed internal / non-commercial** for MVP; commercial consent drafts ready but not yet granted |
| Week 1 status | **Satisfied on `main`** via merged PR #1 |

## Week 1 exit criteria (from Phase 0 plan)

| Criterion | Evidence |
|-----------|----------|
| Repo + Compose (Postgres/pgvector, MinIO) | `docker-compose.yml`, `.env.example` |
| Migrations | `packages/db/migrations/001_init.sql` |
| Audit template filled for MCHK+DCHK | `docs/SOURCE_LICENSING_AUDIT.md` |
| Fixture SOP | `scripts/download_checklist.md` |
| Fixtures hashed / immutable ingest | `services/worker` + `fixtures/manifests/m1.jsonl` |
| Idempotent ingest | Unit tests in `tests/` |

## Next gate

Weeks 2–6 require a separate milestone approval. Do not start live adapters or real LLM providers without that approval and an updated DPA/licence review.

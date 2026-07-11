# Contributing — RegLens HK

1. Read `AGENTS.md` before changing extraction, provenance, or licensing behaviour.
2. Use synthetic fixtures under `fixtures/synthetic/` only in Git.
3. Place real manually acquired documents in gitignored `private-data/` (see `docs/PRIVATE_DATA.md`).
4. Run `make verify` before opening a PR.
5. Do not add scrapers, real LLM network calls, OCR, NCHK, or semantic search without an explicit milestone approval.
6. Prefer deterministic parsing and schema-validated extraction with evidence spans.

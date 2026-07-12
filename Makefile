.PHONY: verify test lint typecheck fixtures web-ci studio-ci site-ci lock \
	lawtrace-deps \
	demo-ingest demo-release demo-enqueue worker-once studio-dev site-dev \
	site-build pages-artifact public-scan \
	integration db-up db-down db-reset-local db-migrate db-status \
	postgres-demo-pipeline postgres-demo-release \
	site-build-from-postgres-release rc2-acceptance \
	rc3-verify sources-status source-sync-mchk-dry source-sync-dchk-dry \
	source-parser-tests ocr-tests core50-status extraction-eval \
	core10-report rc4-verify

PYTHONPATH := services/worker
export PYTHONPATH

# Default local Compose DSN (local-only credentials — never production).
COMPOSE_DATABASE_URL ?= postgresql://reglens:reglens_local_only@127.0.0.1:5432/reglens
DEFAULT_MANIFEST ?= fixtures/manifests/m1.jsonl
DEFAULT_DATA_ROOT ?= data
PG_RELEASE_OUT ?= generated/public-release-pg
RC3_TEST_PATHS := tests/sources tests/ocr tests/llm tests/pipeline
RC3_RUFF_PATHS := $(RC3_TEST_PATHS)

verify: fixtures lint typecheck test studio-ci demo-release public-scan site-ci
	@echo "All MVP-RC1 / RC2 demo-mode verification targets passed"
	@echo "Note: make verify is the RC2 demo-mode gate (REGLENS_MODE=demo / no DATABASE_URL)."
	@echo "      Postgres path: make integration / make postgres-demo-pipeline (requires DATABASE_URL)."

test:
	pytest

lint:
	ruff check services/worker tests scripts
	ruff format --check services/worker tests scripts

typecheck:
	mypy

fixtures:
	python scripts/check_fixtures.py

studio-ci:
	cd apps/studio && npm ci && npm run typecheck && npm run build

site-ci: pages-artifact
	cd apps/site && npm ci && npm run typecheck && npm run build

# Back-compat alias
web-ci: studio-ci

demo-ingest:
	rm -rf data
	python -m reglens_worker ingest \
	  --manifest $(DEFAULT_MANIFEST) \
	  --data-root $(DEFAULT_DATA_ROOT) \
	  --demo-auto-approve-synthetic

demo-release: demo-ingest
	rm -rf generated/public-release
	python -m reglens_worker release build \
	  --data-root $(DEFAULT_DATA_ROOT) \
	  --annotations publications/demo/editorial_annotations.v1.json \
	  --policy publications/policies/source_publication_policy.v1.json \
	  --taxonomy publications/taxonomy/taxonomy.v1.json \
	  --release-id demo-0.1.0 \
	  --release-mode synthetic_demo \
	  --released-at 2026-07-11T00:00:00Z \
	  --output generated/public-release
	python scripts/check_public_release.py generated/public-release

public-scan:
	python scripts/check_public_release.py generated/public-release

pages-artifact: demo-release
	rm -rf apps/site/public/data/release
	mkdir -p apps/site/public/data/release
	cp -R generated/public-release/. apps/site/public/data/release/
	touch apps/site/public/.nojekyll

# --- RC2 demo / worker helpers (demo mode by default) ---

demo-enqueue:
	python -m reglens_worker ingest enqueue \
	  --manifest $(DEFAULT_MANIFEST) \
	  --data-root $(DEFAULT_DATA_ROOT)

worker-once:
	python -m reglens_worker worker run-once \
	  --data-root $(DEFAULT_DATA_ROOT) \
	  --demo-auto-approve-synthetic

studio-dev:
	cd apps/studio && npm run dev

site-dev:
	cd apps/site && npm run dev

site-build: pages-artifact
	cd apps/site && npm run build

# --- Postgres / Compose (RC2) ---

integration:
	@if [ -z "$${DATABASE_URL}" ]; then \
	  if [ -n "$${CI}" ] || [ "$${GITHUB_ACTIONS}" = "true" ]; then \
	    echo "ERROR: DATABASE_URL is required for make integration in CI" >&2; \
	    exit 1; \
	  fi; \
	  echo "Skipping integration: DATABASE_URL unset (local). Set DATABASE_URL or use CI postgres-integration job."; \
	  exit 0; \
	fi; \
	REGLENS_MODE=postgres pytest -m integration; \
	REGLENS_MODE=postgres pytest tests/pg tests/test_jobs_postgres.py tests/test_release_equivalence.py

db-up:
	@if ! command -v docker >/dev/null 2>&1; then \
	  echo "ERROR: docker not found. Install Docker Desktop/Engine, then re-run make db-up." >&2; \
	  echo "See docs/LOCAL_SETUP.md and docs/OPERATIONS.md." >&2; \
	  exit 1; \
	fi
	docker compose up -d db minio
	@echo "Postgres/MinIO starting. After healthy: export DATABASE_URL='$(COMPOSE_DATABASE_URL)'"
	@echo "Then apply schema: make db-migrate   # mount alone does NOT run RC2 migrations"

db-down:
	@if ! command -v docker >/dev/null 2>&1; then \
	  echo "ERROR: docker not found; cannot stop Compose services." >&2; \
	  exit 1; \
	fi
	docker compose down

db-reset-local:
	@echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	@echo "WARNING: DESTRUCTIVE — drops and recreates the LOCAL Postgres DB."
	@echo "Only localhost / 127.0.0.1 / ::1 / docker 'db' hosts are allowed."
	@echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
	@URL="$${DATABASE_URL:-$(COMPOSE_DATABASE_URL)}"; \
	export DATABASE_URL="$$URL"; \
	python -c "from reglens_worker.mode import assert_local_database_url; import os; print(assert_local_database_url(os.environ['DATABASE_URL']))"; \
	if command -v docker >/dev/null 2>&1; then \
	  echo "Resetting via docker compose (volume wipe + recreate)..."; \
	  docker compose down -v; \
	  docker compose up -d db; \
	  echo "Waiting for Postgres..."; \
	  for i in 1 2 3 4 5 6 7 8 9 10 11 12; do \
	    docker compose exec -T db pg_isready -U reglens -d reglens && break; \
	    sleep 2; \
	  done; \
	  echo "Apply migrations with: make db-migrate"; \
	  echo "(Init SQL mount is NOT sufficient for RC2 — see docs/DATABASE_MIGRATIONS.md)"; \
	elif command -v psql >/dev/null 2>&1; then \
	  echo "docker unavailable — falling back to psql DROP/CREATE DATABASE."; \
	  echo "See docs/OPERATIONS.md if this fails (role must own the DB)."; \
	  psql "$$URL" -v ON_ERROR_STOP=1 -c "SELECT 1" >/dev/null; \
	  DBNAME=$$(python -c "from urllib.parse import urlparse; import os; print(urlparse(os.environ['DATABASE_URL']).path.lstrip('/') or 'reglens')"); \
	  ADMIN_URL=$$(python -c "from urllib.parse import urlparse, urlunparse; import os; u=urlparse(os.environ['DATABASE_URL']); print(urlunparse((u.scheme,u.netloc,'/postgres',u.params,u.query,u.fragment)))"); \
	  psql "$$ADMIN_URL" -v ON_ERROR_STOP=1 -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='$$DBNAME' AND pid <> pg_backend_pid();" || true; \
	  psql "$$ADMIN_URL" -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS \"$$DBNAME\";"; \
	  psql "$$ADMIN_URL" -v ON_ERROR_STOP=1 -c "CREATE DATABASE \"$$DBNAME\";"; \
	  echo "Apply migrations with: make db-migrate"; \
	else \
	  echo "ERROR: neither docker nor psql is available for db-reset-local." >&2; \
	  echo "Install Docker (preferred) or PostgreSQL client tools, then retry." >&2; \
	  echo "Documented in docs/OPERATIONS.md / docs/LOCAL_SETUP.md." >&2; \
	  exit 1; \
	fi

db-migrate:
	@if [ -z "$${DATABASE_URL}" ]; then \
	  echo "ERROR: DATABASE_URL is required for make db-migrate" >&2; \
	  echo "Example: export DATABASE_URL='$(COMPOSE_DATABASE_URL)'" >&2; \
	  exit 1; \
	fi
	REGLENS_MODE=postgres python -m reglens_worker db migrate

db-status:
	@if [ -z "$${DATABASE_URL}" ]; then \
	  echo "ERROR: DATABASE_URL is required for make db-status" >&2; \
	  exit 1; \
	fi
	REGLENS_MODE=postgres python -m reglens_worker db status

postgres-demo-pipeline:
	@if [ -z "$${DATABASE_URL}" ]; then \
	  echo "ERROR: DATABASE_URL is required for make postgres-demo-pipeline" >&2; \
	  exit 1; \
	fi
	REGLENS_MODE=postgres python scripts/postgres_demo_pipeline.py

postgres-demo-release:
	@if [ ! -d "$(PG_RELEASE_OUT)" ]; then \
	  echo "ERROR: $(PG_RELEASE_OUT) missing — run make postgres-demo-pipeline first" >&2; \
	  exit 1; \
	fi
	python scripts/check_public_release.py $(PG_RELEASE_OUT)

site-build-from-postgres-release:
	@if [ ! -d "$(PG_RELEASE_OUT)" ]; then \
	  echo "ERROR: $(PG_RELEASE_OUT) missing — run make postgres-demo-pipeline first" >&2; \
	  exit 1; \
	fi
	rm -rf apps/site/public/data/release
	mkdir -p apps/site/public/data/release
	cp -R $(PG_RELEASE_OUT)/. apps/site/public/data/release/
	touch apps/site/public/.nojekyll
	cd apps/site && npm ci && npm run typecheck && npm run build

rc2-acceptance:
	@echo "=== RC2 acceptance: demo-mode gate ==="
	$(MAKE) verify
	@echo "=== RC2 acceptance: postgres path (requires DATABASE_URL) ==="
	@if [ -z "$${DATABASE_URL}" ]; then \
	  if [ -n "$${CI}" ] || [ "$${GITHUB_ACTIONS}" = "true" ]; then \
	    echo "ERROR: DATABASE_URL required for rc2-acceptance in CI" >&2; \
	    exit 1; \
	  fi; \
	  echo "Skipping postgres acceptance locally (DATABASE_URL unset)."; \
	  exit 0; \
	fi; \
	$(MAKE) integration; \
	$(MAKE) postgres-demo-pipeline; \
	$(MAKE) postgres-demo-release

# --- RC3 source sync / OCR / LLM pilot helpers ---

rc3-verify:
	pytest $(RC3_TEST_PATHS)
	ruff check $(RC3_RUFF_PATHS)
	ruff format --check $(RC3_RUFF_PATHS)

sources-status:
	@echo "RC3 source automation policy (metadata posture only; public availability is not reuse permission; robots.txt is not a licence)"
	@if command -v jq >/dev/null 2>&1; then \
	  jq '.policies[] | {source_id, regulator_code, discovery_mode, document_acquisition, content_use_posture, require_user_agent_contact, public_visibility_policy_ref, publication_caveats}' sources/policies/source_automation_policy.v1.json; \
	else \
	  python -m json.tool sources/policies/source_automation_policy.v1.json; \
	fi

source-sync-mchk-dry:
	python -m reglens_worker sources sync --source mchk_judgments --mode metadata --dry-run \
	  --fixture-dir fixtures/source_html

source-sync-dchk-dry:
	python -m reglens_worker sources sync --source dchk_judgments --mode metadata --dry-run \
	  --fixture-dir fixtures/source_html

source-parser-tests:
	pytest tests/sources

ocr-tests:
	pytest tests/ocr

core50-status:
	@if command -v jq >/dev/null 2>&1; then \
	  cat publications/pilot/core50.v1.json | jq .; \
	else \
	  cat publications/pilot/core50.v1.json; \
	fi

extraction-eval:
	@echo "RC3 extraction eval placeholder: publications/pilot/core10_eval.v1.json"

# --- RC4 Core10 / public Observatory enrichment ---

core10-report: demo-release
	python scripts/core10_report.py \
	  --release-dir generated/public-release \
	  --output-dir reports/core10

rc4-verify: verify core10-report
	pytest tests/test_rc4_public_pages.py

lock:
	pip install -r services/worker/requirements.txt
	pip freeze > services/worker/requirements.lock.txt
	@if [ -f services/lawtrace-worker/requirements.txt ]; then \
		pip install -r services/lawtrace-worker/requirements.txt; \
	fi

lawtrace-deps:
	pip install -r services/lawtrace-worker/requirements.txt

.PHONY: verify test lint typecheck fixtures web-ci studio-ci site-ci lock \
	demo-ingest demo-release studio-dev site-dev site-build pages-artifact \
	public-scan

PYTHONPATH := services/worker
export PYTHONPATH

verify: fixtures lint typecheck test studio-ci demo-release public-scan site-ci
	@echo "All MVP-RC1 verification targets passed"

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
	  --manifest fixtures/manifests/m1.jsonl \
	  --data-root data \
	  --demo-auto-approve-synthetic

demo-release: demo-ingest
	rm -rf generated/public-release
	python -m reglens_worker release build \
	  --data-root data \
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

studio-dev:
	cd apps/studio && npm run dev

site-dev:
	cd apps/site && npm run dev

site-build: pages-artifact
	cd apps/site && npm run build

lock:
	pip install -r services/worker/requirements.txt
	pip freeze > services/worker/requirements.lock.txt

.PHONY: verify test lint typecheck fixtures web-ci lock

verify: fixtures lint typecheck test web-ci
	@echo "All Milestone 2A verification targets passed"

test:
	PYTHONPATH=services/worker pytest

lint:
	ruff check services/worker tests scripts
	ruff format --check services/worker tests scripts

typecheck:
	mypy

fixtures:
	python scripts/check_fixtures.py

web-ci:
	cd apps/web && npm ci && npm run typecheck && npm run build

lock:
	pip install -r services/worker/requirements.txt
	pip freeze > services/worker/requirements.lock.txt

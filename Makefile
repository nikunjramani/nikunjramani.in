# nikunjramani.in — one entry point per task.
# CI runs these same targets, so "works locally, fails in CI" has one less cause.

SHELL := /bin/bash
.DEFAULT_GOAL := help

PYTHON  := /opt/homebrew/bin/python3.13
BACKEND := backend/functions
FRONT   := frontend
VENV    := $(BACKEND)/.venv

.PHONY: help setup setup-frontend setup-backend dev dev-frontend dev-emulators \
        gen validate lint lint-frontend lint-backend lint-infra test test-frontend \
        test-backend build deploy clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

# ── setup ───────────────────────────────────────────────────────────
setup: setup-backend setup-frontend ## Install all dependencies

setup-backend:
	cd $(BACKEND) && uv venv --python $(PYTHON) && uv sync --all-extras

setup-frontend:
	cd $(FRONT) && npm install

# ── develop ─────────────────────────────────────────────────────────
dev: ## Next.js dev server + Firebase emulators
	@trap 'kill 0' EXIT; $(MAKE) dev-emulators & $(MAKE) dev-frontend & wait

dev-frontend:
	cd $(FRONT) && npm run dev

dev-emulators:
	firebase emulators:start --import=./.emulator-data --export-on-exit=./.emulator-data

# ── generate ────────────────────────────────────────────────────────
gen: ## Regenerate all models from architecture/schemas
	./architecture/codegen/generate.sh

validate: ## Validate schemas and example fixtures
	$(PYTHON) architecture/codegen/validate.py

# ── quality ─────────────────────────────────────────────────────────
lint: lint-backend lint-frontend lint-infra ## Lint everything

lint-backend:
	cd $(BACKEND) && uv run ruff check . && uv run ruff format --check . \
		&& uv run mypy . && uv run lint-imports

lint-frontend:
	cd $(FRONT) && npx tsc --noEmit && npm run lint

lint-infra:
	terraform -chdir=infra/terraform/envs/prod fmt -check -recursive

test: test-backend test-frontend ## Run all tests

test-backend:
	cd $(BACKEND) && uv run pytest

test-frontend:
	cd $(FRONT) && npm test --if-present

# ── ship ────────────────────────────────────────────────────────────
build: ## Production build of both sides
	cd $(FRONT) && npm run build

deploy: ## terraform apply, then deploy rules + functions
	terraform -chdir=infra/terraform/envs/prod apply
	firebase deploy --only firestore:rules,firestore:indexes,storage
	firebase deploy --only functions

clean: ## Remove build artefacts and caches
	rm -rf $(FRONT)/.next $(FRONT)/node_modules $(VENV)
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -prune -exec rm -rf {} + 2>/dev/null || true

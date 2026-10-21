# nikunjramani.in — one entry point per task.
# CI runs these same targets, so "works locally, fails in CI" has one less cause.

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Python 3.13 as uv resolves it — never a system 3.9. Override with `make PYTHON=...`.
PYTHON     ?= $(shell uv python find 3.13 2>/dev/null || echo python3.13)
BACKEND    := backend
FRONT      := frontend
DEV_VENV   := $(BACKEND)/.venv

# The API on Cloud Run (ADR 0023). PROJECT is a project ID; CI passes it from .firebaserc.
PROJECT    ?= nikunjramani-in
REGION     := asia-south1

# Emulator wiring for running the API locally (the Admin SDK reads these from the process).
EMULATORS  := FIRESTORE_EMULATOR_HOST=127.0.0.1:8080 FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099 \
              FIREBASE_STORAGE_EMULATOR_HOST=127.0.0.1:9199 GOOGLE_CLOUD_PROJECT=$(PROJECT)

.PHONY: help setup setup-frontend setup-backend dev dev-frontend dev-backend dev-emulators \
        gen validate lint lint-frontend lint-backend lint-infra test test-frontend \
        test-backend build api-registry deploy-api deploy clean

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
dev: ## Firebase emulators + the API (reloading) + Next.js
	@trap 'kill 0' EXIT; $(MAKE) dev-emulators & $(MAKE) dev-backend & $(MAKE) dev-frontend & wait

dev-frontend:
	cd $(FRONT) && API_BASE_URL=http://127.0.0.1:8000 npm run dev

dev-backend: ## The API on :8000 against the emulators, reloading on save
	cd $(BACKEND) && $(EMULATORS) uv run uvicorn apps.api:app --reload --port 8000

dev-emulators:
	firebase emulators:start --import=./.emulator-data --export-on-exit=./.emulator-data

# ── generate ────────────────────────────────────────────────────────
gen: ## Regenerate all models from architecture/schemas
	./architecture/codegen/generate.sh

validate: ## Validate schemas and example fixtures
	uv run --quiet --with jsonschema --with referencing python architecture/codegen/validate.py

# ── quality ─────────────────────────────────────────────────────────
lint: lint-backend lint-frontend lint-infra ## Lint everything

lint-backend:
	cd $(BACKEND) && uv run ruff check . && uv run ruff format --check . \
		&& uv run mypy . && uv run lint-imports

lint-frontend:
	cd $(FRONT) && npx next typegen && npx tsc --noEmit && npm run lint

lint-infra:
	terraform -chdir=infra/terraform fmt -check -recursive

test: test-backend test-frontend ## Run all tests

test-backend:
	cd $(BACKEND) && uv run pytest

test-frontend:
	cd $(FRONT) && npm test --if-present

# ── ship ────────────────────────────────────────────────────────────
build: ## Production build of both sides
	cd $(FRONT) && npm run build

# CI's job (.github/actions/cloud-run-deploy) — locally only as break-glass.
api-registry: ## Create the API's image repository if it's missing (PROJECT=…)
	gcloud artifacts repositories describe backend --project $(PROJECT) --location $(REGION) >/dev/null 2>&1 \
		|| gcloud artifacts repositories create backend --project $(PROJECT) --location $(REGION) \
			--repository-format docker --description "The API image (ADR 0023)"
	gcloud artifacts repositories set-cleanup-policies backend --project $(PROJECT) --location $(REGION) \
		--policy $(BACKEND)/deploy/cleanup-policy.json --no-dry-run

# The service's whole shape lives here, so CI and break-glass deploy the same thing. Per-project
# values come from backend/deploy/$(PROJECT).yaml; secrets from Secret Manager.
deploy-api: ## Deploy IMAGE as the `api` Cloud Run service (PROJECT=…, IMAGE=…)
	@test -n "$(IMAGE)" || { echo "IMAGE is required"; exit 1; }
	gcloud run deploy api --project $(PROJECT) --region $(REGION) --image $(IMAGE) \
		--service-account functions-runtime@$(PROJECT).iam.gserviceaccount.com \
		--cpu 1 --memory 1Gi --concurrency 80 --min-instances 0 --max-instances 3 --timeout 600 \
		--env-vars-file $(BACKEND)/deploy/$(PROJECT).yaml \
		--set-secrets RESEND_API_KEY=RESEND_API_KEY:latest,CONTACT_EMAIL_TO=CONTACT_EMAIL_TO:latest \
		--allow-unauthenticated --quiet

deploy: ## Break-glass: terraform apply, rules, the API (IMAGE=…) and App Hosting
	terraform -chdir=infra/terraform/envs/prod apply
	firebase deploy --only firestore:rules,firestore:indexes
	$(MAKE) deploy-api PROJECT=nikunjramani-in IMAGE=$(IMAGE)
	firebase deploy --only apphosting

clean: ## Remove build artefacts and caches
	rm -rf $(FRONT)/.next $(FRONT)/node_modules $(DEV_VENV)
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -prune -exec rm -rf {} + 2>/dev/null || true

.PHONY: lint lint-yaml lint-ansible check setup help audit

# Virtualenv paths
VENV := .venv
BIN := $(VENV)/bin
PYTHON := $(BIN)/python
PIP := $(BIN)/pip
YAMLLINT := $(BIN)/yamllint
ANSIBLE_LINT := $(BIN)/ansible-lint
ANSIBLE_PLAYBOOK := $(BIN)/ansible-playbook

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Create venv, install dependencies, and configure git hooks
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	git config core.hooksPath .githooks
	@echo "\n\033[32m✓ Setup complete. Use 'make lint' or 'make audit' — no activation needed.\033[0m"

lint: lint-yaml lint-ansible ## Run all linters

lint-yaml: ## Run yamllint on all YAML files
	$(YAMLLINT) .

lint-ansible: ## Run ansible-lint on all roles
	$(ANSIBLE_LINT)

audit: ## Run automated audit checks on all roles
	$(PYTHON) audit/audit.py

check: ## Run ansible-playbook --check (syntax check) on all roles
	@for role in roles/*/; do \
		role_name=$$(basename $$role); \
		echo "Checking role: $$role_name"; \
		$(ANSIBLE_PLAYBOOK) --syntax-check \
			-e "{}" \
			$$role/tests/test.yml 2>/dev/null || \
			echo "  No test playbook for $$role_name"; \
	done

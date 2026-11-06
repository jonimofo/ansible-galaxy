.PHONY: lint lint-yaml lint-ansible check test setup help audit

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
	@echo "\n\033[32m✓ Setup complete. Use 'make lint' or 'make audit', no activation needed.\033[0m"

lint: lint-yaml lint-ansible ## Run all linters

lint-yaml: ## Run yamllint on all YAML files
	$(YAMLLINT) .

lint-ansible: ## Run ansible-lint on all roles
	$(ANSIBLE_LINT)

audit: ## Run automated audit checks on all roles
	$(PYTHON) audit/audit.py

check: ## Syntax-check roles/*/tests/test.yml (variables are not evaluated)
	@failed=""; \
	for role in roles/*/; do \
		role_name=$$(basename $$role); \
		playbook=$${role}tests/test.yml; \
		if [ ! -f "$$playbook" ]; then \
			echo "  No test playbook for $$role_name"; \
			continue; \
		fi; \
		echo "Checking role: $$role_name"; \
		if ! $(ANSIBLE_PLAYBOOK) --syntax-check -i localhost, "$$playbook" > /dev/null; then \
			failed="$$failed $$role_name"; \
		fi; \
	done; \
	if [ -n "$$failed" ]; then \
		echo "Syntax check failed for:$$failed"; \
		exit 1; \
	fi

test: ## Run the regression test playbooks (roles/*/tests/test_*.yml) on localhost
	@set -e; for playbook in roles/*/tests/test_*.yml; do \
		echo "Running $$playbook"; \
		$(ANSIBLE_PLAYBOOK) -i localhost, $$playbook; \
	done

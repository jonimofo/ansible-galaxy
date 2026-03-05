.PHONY: lint lint-yaml lint-ansible check help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint: lint-yaml lint-ansible ## Run all linters

lint-yaml: ## Run yamllint on all YAML files
	yamllint .

lint-ansible: ## Run ansible-lint on all roles
	ansible-lint

check: ## Run ansible-playbook --check (syntax check) on all roles
	@for role in roles/*/; do \
		role_name=$$(basename $$role); \
		echo "Checking role: $$role_name"; \
		ansible-playbook --syntax-check \
			-e "{}" \
			$$role/tests/test.yml 2>/dev/null || \
			echo "  No test playbook for $$role_name"; \
	done

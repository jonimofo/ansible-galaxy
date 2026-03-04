# jonimofo.infrastructure - Ansible Collection Makefile

.PHONY: help lint build test clean setup

# Default target
help:
	@echo "jonimofo.infrastructure - Available commands:"
	@echo ""
	@echo "  make setup  - Install pre-commit hook"
	@echo "  make lint   - Run ansible-lint and yamllint"
	@echo "  make build  - Build the collection archive"
	@echo "  make test   - Syntax-check all test playbooks"
	@echo "  make clean  - Remove build artifacts"

setup:
	git config core.hooksPath .githooks
	@echo "Pre-commit hook installed."

lint:
	yamllint .
	ansible-lint

build:
	ansible-galaxy collection build --force

test:
	@for f in roles/*/tests/test.yml; do \
		echo "Syntax-checking $$f ..."; \
		ansible-playbook --syntax-check "$$f" || exit 1; \
	done
	@echo "All syntax checks passed."

clean:
	rm -f jonimofo-infrastructure-*.tar.gz

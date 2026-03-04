# jonimofo.infrastructure - Ansible Collection Makefile

.PHONY: help lint build test clean

# Default target
help:
	@echo "jonimofo.infrastructure - Available commands:"
	@echo ""
	@echo "  make lint   - Run ansible-lint and yamllint"
	@echo "  make build  - Build the collection archive"
	@echo "  make test   - Syntax-check all test playbooks"
	@echo "  make clean  - Remove build artifacts"

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

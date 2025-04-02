# Development commands
.PHONY: dev test test-cov lint typecheck format precommit check

# Run development server
dev:
	@echo "Starting development server..."
	@echo "Press Ctrl+C to stop"
	uv run dev

# Run tests
test:
	python scripts/bash_runner.py run_test

# Run tests with coverage
test-cov:
	python scripts/bash_runner.py run_test_cov

# Run linters
lint:
	python scripts/bash_runner.py run_lint

# Run type checking
typecheck:
	python scripts/bash_runner.py run_typecheck

# Run code formatters
format:
	python scripts/bash_runner.py run_format

# Run pre-commit hooks
precommit:
	python scripts/bash_runner.py run_precommit

# Run all checks
check:
	python scripts/bash_runner.py run_check

# Database commands
.PHONY: db-init db-migrate db-create-migration setup

# Initialize database
db-init:
	python scripts/bash_runner.py run_db_init

# Run database migrations
db-migrate:
	python scripts/bash_runner.py run_db_migrate

# Create new database migration
db-create-migration:
	@if [ "$(message)" = "" ]; then \
		echo "Error: message is required. Usage: make db-create-migration message=\"your message\""; \
		exit 1; \
	fi
	python scripts/bash_runner.py run_db_create_migration "$(message)"

# Run full setup
setup:
	python scripts/bash_runner.py run_setup

# Utility commands
.PHONY: copy-iso copy-ulid copy-uuid

# Copy ISO timestamp to clipboard
copy-iso:
	python scripts/bash_runner.py copy_iso

# Copy ULID to clipboard
copy-ulid:
	python scripts/bash_runner.py copy_ulid

# Copy UUID to clipboard
copy-uuid:
	python scripts/bash_runner.py copy_uuid

# Help command
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  Development:"
	@echo "    make dev              - Run development server"
	@echo "    make test             - Run tests"
	@echo "    make test-cov         - Run tests with coverage"
	@echo "    make lint             - Run linters"
	@echo "    make typecheck        - Run type checking"
	@echo "    make format           - Run code formatters"
	@echo "    make precommit        - Run pre-commit hooks"
	@echo "    make check            - Run all checks"
	@echo ""
	@echo "  Database:"
	@echo "    make db-init          - Initialize database"
	@echo "    make db-migrate       - Run database migrations"
	@echo "    make db-create-migration message=\"your message\" - Create new migration"
	@echo "    make setup            - Run full setup (init DB and tests)"
	@echo ""
	@echo "  Utilities:"
	@echo "    make copy-iso         - Copy ISO timestamp to clipboard"
	@echo "    make copy-ulid        - Copy ULID to clipboard"
	@echo "    make copy-uuid        - Copy UUID to clipboard"
	@echo ""
	@echo "  Help:"
	@echo "    make help             - Show this help message"

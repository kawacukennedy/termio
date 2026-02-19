# ============================================================================
# TERMIO — Development Makefile
# ============================================================================

.PHONY: setup build dev test lint clean run-server run-tui run-ai help

# Default target
help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================================================
# Setup
# ============================================================================

setup: ## Install all dependencies (Rust + Python)
	@echo "==> Installing Rust toolchain..."
	rustup update stable
	rustup component add rustfmt clippy
	@echo "==> Installing Python dependencies..."
	cd ai_service && pip install -e ".[dev]" 2>/dev/null || cd ai_service && poetry install
	@echo "==> Setup complete!"

# ============================================================================
# Build
# ============================================================================

build: ## Build all Rust crates (release)
	cargo build --workspace --release

build-debug: ## Build all Rust crates (debug)
	cargo build --workspace

check: ## Type-check without building
	cargo check --workspace

# ============================================================================
# Development
# ============================================================================

dev: ## Start all services (server + AI service)
	@echo "Starting TERMIO services..."
	@$(MAKE) run-ai &
	@sleep 2
	@$(MAKE) run-server

run-server: ## Run the HTTP server
	cargo run -p termio-server

run-tui: ## Run the terminal UI
	cargo run -p termio-tui

run-ai: ## Run the Python AI service
	cd ai_service && uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# ============================================================================
# Testing
# ============================================================================

test: test-unit test-integration ## Run all tests

test-unit: ## Run unit tests
	cargo test --workspace
	cd ai_service && python -m pytest tests/ -v 2>/dev/null || true

test-integration: ## Run integration tests
	cargo test --workspace -- --ignored 2>/dev/null || true

test-coverage: ## Run tests with coverage
	cargo llvm-cov --workspace --html
	@echo "Coverage report: target/llvm-cov/html/index.html"

# ============================================================================
# Linting & Formatting
# ============================================================================

lint: ## Run all linters
	@echo "==> Rust: clippy..."
	cargo clippy --workspace -- -D warnings
	@echo "==> Rust: format check..."
	cargo fmt --all -- --check
	@echo "==> Python: ruff..."
	cd ai_service && ruff check src/ 2>/dev/null || true
	@echo "==> Python: mypy..."
	cd ai_service && mypy src/ 2>/dev/null || true

fmt: ## Auto-format all code
	cargo fmt --all
	cd ai_service && ruff format src/ 2>/dev/null || true

# ============================================================================
# Database
# ============================================================================

db-migrate: ## Run database migrations
	sqlite3 termio.db < migrations/001_initial.sql

db-reset: ## Reset database
	rm -f termio.db
	$(MAKE) db-migrate

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start Docker services
	docker-compose up -d

docker-down: ## Stop Docker services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f

# ============================================================================
# Security
# ============================================================================

audit: ## Run security audit
	cargo audit
	cd ai_service && pip-audit 2>/dev/null || true

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean build artifacts
	cargo clean
	rm -rf ai_service/__pycache__ ai_service/.mypy_cache
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -delete

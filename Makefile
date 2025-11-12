# Makefile for OpenAI Assistant Orchestrator
# Common development tasks

.PHONY: help install dev test lint fmt type clean build run migrate smoke

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install dependencies
	cd backend && pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov black isort flake8 mypy
	pip install pre-commit
	pre-commit install

dev: ## Install dev dependencies
	cd backend && pip install -e .
	pip install ipython ipdb

test: ## Run unit tests
	cd backend && pytest tests/ -v

test-cov: ## Run tests with coverage
	cd backend && pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	@echo "Coverage report: backend/htmlcov/index.html"

lint: ## Run linters
	cd backend && flake8 app/ tests/ --max-line-length=79 --extend-ignore=E203,W503
	cd backend && mypy app/ --ignore-missing-imports --no-strict-optional

fmt: ## Format code
	cd backend && black app/ tests/ --line-length=79
	cd backend && isort app/ tests/ --profile=black --line-length=79

type: ## Type check with mypy
	cd backend && mypy app/ --ignore-missing-imports --no-strict-optional

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf backend/htmlcov backend/.coverage backend/.pytest_cache

build: ## Build Docker image
	docker build -t orchestrator:latest ./backend

run: ## Run with Docker Compose
	docker-compose -f compose.core.yml up -d

stop: ## Stop Docker Compose services
	docker-compose -f compose.core.yml down

logs: ## Show Docker Compose logs
	docker-compose -f compose.core.yml logs -f

migrate: ## Run database migrations
	psql -U opa -d opa -f backend/migrations/001_initial_schema.sql
	psql -U opa -d opa -f backend/migrations/002_hybrid_search_functions.sql

smoke: ## Run smoke tests
	bash scripts/smoke_orchestrate.sh

smoke-ps: ## Run smoke tests (PowerShell)
        powershell -File scripts/smoke_orchestrate.ps1

serve-frontend: ## Start the React admin settings dev server for live preview
        bash scripts/serve_frontend.sh

db-shell: ## Open PostgreSQL shell
	psql -U opa -d opa

redis-cli: ## Open Redis CLI
	redis-cli

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

up: ## Start all services
	docker-compose -f compose.core.yml up -d
	@echo "Services started. Check status with: make ps"

ps: ## Show running services
	docker-compose -f compose.core.yml ps

restart: ## Restart all services
	docker-compose -f compose.core.yml restart

shell: ## Open backend shell
	cd backend && python -m IPython

.PHONY: help

CURRENT_DIR = $(shell pwd)
GREEN = \033[0;32m
YELLOW = \033[0;33m
NC = \033[0m

APP_HOST := $(or ${APP_HOST},${APP_HOST},0.0.0.0)
APP_PORT := $(or ${APP_PORT},${APP_PORT},5000)
PYTHONPATH := $(or ${PYTHONPATH},${PYTHONPATH},.)

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-17s\033[0m %s\n", $$1, $$2}'

# ============= General use-cases =============

start-up: dependencies-up install migrate start ## Start service from zero
check: linting test ## Linting python code and run tests in one command

# ============= General commands =============

install: ## Install all dependencies (need poetry!)
	@echo "\n${GREEN}Installing project dependencies${NC}"
	pip install --force-reinstall poetry
	poetry install

dependencies-up: ## Pull and start the Docker containers with dependencies in the background
	@echo "\n${GREEN}Start the Docker containers with dependencies${NC}"
	docker compose up -d


dependencies-down: ## Down the Docker containers with dependencies
	@echo "\n${GREEN}Down the Docker containers with dependencies${NC}"
	docker-compose down

clean: dependencies-down ## Clear temporary information, stop Docker containers
	@echo "\n${YELLOW}Clear cache directories${NC}"
	rm -rf .mypy_cache .pytest_cache .coverage
	poetry run pyclean .


start: ## Run applications
	@echo "Starting test webserver..."
	python -m \
	uvicorn app.main:app --host ${APP_HOST} --port ${APP_PORT}

test-webserver:
	@echo "Starting test webserver..."
	python -m \
	uvicorn app.main:app --host ${APP_HOST} --port ${APP_PORT} --reload --reload-dir=./app

test:
	pytest ${TARGET}

fmt: ## Auto formatting python code
	@echo "\n${GREEN}Auto formatting python code with isort${NC}"
	poetry run isort . || true
	@echo "\n${GREEN}Auto formatting python code with black${NC}"
	poetry run black . || true

linting: flake8 isort black mypy ## Linting python code

# ============= Other project specific commands =============

flake8: ## Linting python code with flake8
	@echo "\n${GREEN}Linting python code with flake8${NC}"
	poetry run flake8 .

isort: ## Linting python code with isort
	@echo "\n${GREEN}Linting python code with isort${NC}"
	poetry run isort app --check

black: ## Linting python code with black
	@echo "\n${GREEN}Linting python code with black${NC}"
	poetry run black --check app

mypy: ## Linting python code with mypy
	@echo "\n${GREEN}Linting python code with mypy${NC}"
	poetry run mypy app --check-untyped-defs

# Database commands
new_revision: ## Create new revision
	docker compose exec app alembic -c /opt/app/secbot/alembic.ini revision --autogenerate -m "${MESSAGE}"

migrate: ## Migrate the database
	docker compose exec app alembic -c /opt/app/secbot/alembic.ini upgrade head

downgrade: ## Downgrade the database
	docker compose exec app alembic -c /opt/app/secbot/alembic.ini downgrade -1

.PHONY: install dev run test lint fmt docker clean

install:        ## Install runtime + dev dependencies
	pip install -e ".[dev]"

dev:            ## Run the dev server with autoreload
	uvicorn flights_over_me.main:app --reload --host 0.0.0.0 --port 8000

run:            ## Run the server (no reload)
	python -m flights_over_me

test:           ## Run the test suite
	pytest -q

lint:           ## Lint with ruff
	ruff check flights_over_me tests

fmt:            ## Auto-fix lint + format
	ruff check --fix flights_over_me tests
	ruff format flights_over_me tests

docker:         ## Build and run via docker compose
	docker compose up --build

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache *.egg-info

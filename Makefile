.PHONY: install test lint format build clean all

install:
	pip install -e ".[all]"

test:
	pytest tests/ -v --tb=short

test-quick:
	pytest tests/ -q --tb=line

coverage:
	pytest tests/ --cov=financial_dynamics --cov-report=term-missing --cov-report=html

lint:
	ruff check src/ tests/ examples/

format:
	ruff format src/ tests/ examples/
	ruff check --fix src/ tests/ examples/

build:
	python -m hatchling build

clean:
	rm -rf dist/ build/ *.egg-info .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -rf {} +

all: lint test build

.PHONY: help install test lint format pre-push clean

help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies in development mode"
	@echo "  make test        - Run test suite"
	@echo "  make lint        - Run all linters (flake8, pylint, mypy)"
	@echo "  make format      - Format code with black and isort"
	@echo "  make pre-push    - Run comprehensive pre-push checks (REQUIRED before push)"
	@echo "  make clean       - Clean temporary files and caches"

# Install dependencies
install:
	pip install -e ".[dev]"

# Run tests
test:
	pytest tests/ -v

# Run linters
lint:
	@echo "Running flake8..."
	flake8 src/ tests/ scripts/ --count --select=E9,F63,F7,F82 --show-source --statistics
	@echo "Running pylint..."
	pylint src/ tests/ scripts/ --rcfile=pyproject.toml || true
	@echo "Running mypy..."
	mypy src/ --ignore-missing-imports --no-strict-optional || true

# Format code
format:
	@echo "Running black..."
	black src/ tests/ scripts/
	@echo "Running isort..."
	isort src/ tests/ scripts/ --profile black

# Pre-push verification (REQUIRED before push)
pre-push:
	@echo "Running pre-push verification..."
	@bash scripts/pre-push-check.sh

# Clean temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/

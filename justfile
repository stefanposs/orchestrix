# Orchestrix Development Commands
# Install just: https://github.com/casey/just

# Default recipe to display help information
default:
    @just --list

# ============================================================================
# Setup & Installation
# ============================================================================

# Install all dependencies including dev dependencies
install:
    uv sync --all-extras --dev

# Install pre-commit hooks
setup-hooks:
    uv run pre-commit install

# Full development setup
setup: install setup-hooks
    @echo "✅ Development environment ready!"

# ============================================================================
# Testing
# ============================================================================

# Run all tests
test:
    uv run pytest

# Run tests with verbose output
test-verbose:
    uv run pytest -v

# Run tests with coverage report
test-cov:
    uv run pytest --cov=orchestrix --cov-report=term-missing

# Run tests with HTML coverage report
test-cov-html:
    uv run pytest --cov=orchestrix --cov-report=html
    @echo "📊 Coverage report: htmlcov/index.html"

# Run tests and generate XML coverage for CI
test-ci:
    uv run pytest --cov=orchestrix --cov-report=xml --cov-report=term

# Run specific test file
test-file FILE:
    uv run pytest {{FILE}} -v

# Watch mode: run tests on file changes
test-watch:
    uv run pytest-watch

# ============================================================================
# Code Quality
# ============================================================================

# Run all QA checks (lint, format-check, typecheck, test)
qa: lint format-check test
    @echo "✅ All QA checks passed!"

# Run ruff linter
lint:
    uv run ruff check .

# Fix linting issues automatically
lint-fix:
    uv run ruff check --fix .

# Check code formatting with ruff
format-check:
    uv run ruff format --check .

# Format code with ruff
format:
    uv run ruff format .

# Run ty type checker (Astral)
ty:
    uv run ty check .

# Run ty with verbose output
ty-verbose:
    uv run ty check . --verbose

# ============================================================================
# Combined Workflows
# ============================================================================

# Fix all auto-fixable issues (format + lint-fix)
fix: format lint-fix
    @echo "✅ Code formatted and linted!"

# Run pre-commit hooks on all files
pre-commit:
    uv run pre-commit run --all-files

# Full check before commit (format, lint, typecheck, ty, test)
check: format lint test
    @echo "✅ Ready to commit!"

# ============================================================================
# Build & Package
# ============================================================================

# Clean build artifacts
clean:
    rm -rf output/dist/ build/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov
    find . -type d -name __pycache__ -exec rm -rf {} +
    @echo "✅ Cleaned build artifacts"

# Build package
build: clean
    uv build
    @echo "✅ Package built in dist/"

# Build and check package with twine
build-check: build
    uv run twine check dist/*

# ============================================================================
# Documentation
# ============================================================================

# Serve documentation locally
docs:
    uv run mkdocs serve

# Build documentation
docs-build:
    uv run mkdocs build

# Deploy documentation to GitHub Pages
docs-deploy:
    uv run mkdocs gh-deploy

# ============================================================================
# Development Tools
# ============================================================================

# Update dependencies
update:
    uv lock --upgrade

# Show outdated dependencies
outdated:
    uv pip list --outdated

# Open Python REPL with orchestrix imported
repl:
    uv run python -c "from orchestrix import *; from orchestrix.infrastructure import *; print('Orchestrix loaded. Available: Message, Command, Event, Module, InMemoryMessageBus, InMemoryEventStore')"

# Run Python REPL
shell:
    uv run python

# ============================================================================
# CI/CD Simulation
# ============================================================================

# Simulate CI pipeline locally
ci: clean install pre-commit test-ci
    @echo "✅ CI simulation complete!"

# Quick CI check (faster, skips some steps)
ci-quick: lint test
    @echo "✅ Quick CI check complete!"

# ============================================================================
# Release Management
# ============================================================================

# Show current version
version:
    @grep '^version = ' pyproject.toml | cut -d'"' -f2

# Prepare release (run all checks)
release-prep: clean qa build-check
    @echo "✅ Release preparation complete!"
    @echo "📦 Version: $(just version)"
    @echo "Next steps:"
    @echo "  1. Update CHANGELOG.md"
    @echo "  2. git tag v$(just version)"
    @echo "  3. git push origin v$(just version)"
    @echo "  4. Create GitHub Release"

# ============================================================================
# Utility Commands
# ============================================================================

# Show project info
info:
    @echo "Project: Orchestrix"
    @echo "Version: $(just version)"
    @echo "Python: $(uv run python --version)"
    @uv tree | head -20

# Count lines of code
loc:
    @echo "Source code:"
    @find components bases projects -name '*.py' | xargs wc -l | tail -1
    @echo "Tests:"
    @find tests -name '*.py' | xargs wc -l | tail -1
    @echo "Total:"
    @find components bases projects tests -name '*.py' | xargs wc -l | tail -1

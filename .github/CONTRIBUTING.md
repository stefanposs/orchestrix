# Contributing to Orchestrix

Thank you for considering contributing to Orchestrix! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to stefan@example.com.

## How to Contribute

### Reporting Bugs

- **Check existing issues** first to avoid duplicates
- **Use the bug report template** when creating a new issue
- **Include details**: OS, Python version, orchestrix version
- **Provide reproduction steps** and expected vs actual behavior

### Suggesting Enhancements

- **Use the feature request template**
- **Explain the use case** and why this enhancement would be useful
- **Describe alternatives** you've considered

### Pull Requests

1. **Fork the repository** and create a new branch from `main`
2. **Make your changes** following our coding standards
3. **Add tests** for any new functionality
4. **Run QA checks**: `just qa` (or see below for individual commands)
5. **Update documentation** if needed
6. **Submit the PR** with a clear description of changes

#### Manual QA Commands

If you don't use `just`, run these commands:

```bash
# Ensure all tests pass
uv run pytest

# Run linters
uv run ruff check . && uv run ruff format .

# Run type checker
uv run ty check
```

## Development Setup

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setup Steps

```bash
# Clone the repository
git clone https://github.com/stefanposs/orchestrix.git
cd orchestrix

# Install dependencies
uv sync --all-extras --dev

# Install pre-commit hooks
uv run pre-commit install

# Or use just for full setup
just setup

# Run tests
just test

# Run with coverage
just test-cov

# Run all QA checks
just qa
```

### Using Just (Recommended)

We provide a `justfile` with common development commands:

```bash
# Install just: https://github.com/casey/just
# On macOS: brew install just

# See all available commands
just

# Common workflows
just check      # Format, lint, test before commit
just fix        # Auto-fix formatting and linting issues
just qa         # Run all quality checks
just ci         # Simulate CI pipeline locally
```

## Code Style

We use the following tools to maintain code quality:

- **Ruff** for linting and formatting
- **Ty** for static type checking
- **Pytest** for testing

### Style Guidelines

- Follow **PEP 8** conventions
- Use **type hints** for all function signatures
- Write **Google-style docstrings** for public APIs
- Keep functions **focused and small** (< 20 lines ideally)
- Aim for **100% test coverage** for new code

## Testing

### Writing Tests

- Place tests in `tests/` directory
- Use descriptive test names: `test_<what>_<scenario>_<expected>`
- Use fixtures from `conftest.py` for common setup
- Test both success and failure scenarios
- Test edge cases

### Running Tests

```bash
# Using just (recommended)
just test              # Run all tests
just test-cov          # Run with coverage report
just test-cov-html     # Generate HTML coverage report
just test-verbose      # Run with verbose output

# Or manually with uv
uv run pytest
uv run pytest --cov=orchestrix --cov-report=html
```

## Documentation

Documentation uses **MkDocs** with the **Material** theme.

### Building Documentation Locally

```bash
# Install docs dependencies
uv sync --extra docs

# Serve documentation locally
uv run mkdocs serve

# Build documentation
uv run mkdocs build
```

### Documentation Guidelines

- Use **Google-style docstrings** in code
- Update **API reference** when adding/changing public APIs
- Add **examples** for new features
- Keep docs **clear and concise**

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat(message): add support for custom metadata
fix(bus): handle empty subscriber list correctly
docs(guide): add event sourcing tutorial
```

## Release Process

Releases are automated through GitHub Actions:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a Git tag: `git tag v0.2.0`
4. Push tag: `git push origin v0.2.0`
5. Create GitHub Release
6. GitHub Actions will build and publish to PyPI

## Getting Help

- 📖 [Documentation](https://orchestrix.readthedocs.io)
- 💬 [GitHub Discussions](https://github.com/stefanposs/orchestrix/discussions)
- 🐛 [Issue Tracker](https://github.com/stefanposs/orchestrix/issues)

## Recognition

Contributors will be recognized in:
- The project README
- Release notes
- GitHub contributors page

Thank you for contributing to Orchestrix! 🎉

# Contributing

Contributions to Orchestrix are welcome. Here is how to get involved.

---

## Setup Development Environment

### 1. Clone the repository

```bash
git clone https://github.com/stefanposs/orchestrix.git
cd orchestrix
```

### 2. Install dependencies

With `just` (recommended):

```bash
just setup
```

Or manually with `uv`:

```bash
uv sync --all-extras --dev
```

### 3. Verify installation

```bash
just test
```

---

## Development Workflow

### Available Commands

```bash
# Setup
just setup              # Initial setup (uv sync)
just install PKG        # Install a package

# Code quality
just fix                # Auto-format and auto-fix code
just qa                 # Run all quality checks (lint + format + type + test)
just check              # Quick check (lint + typecheck only)

# Testing
just test               # Run tests
just test-cov           # Run tests with coverage
just test-watch         # Watch mode — re-run on file change

# Build
just build              # Build package
just clean              # Clean build artifacts

# Documentation
just docs               # Serve documentation locally
just docs-build         # Build documentation
just docs-deploy        # Deploy to GitHub Pages

# CI/CD
just ci                 # Full CI pipeline
```

### Before Committing

```bash
# 1. Auto-format code
just fix

# 2. Run all quality checks
just qa

# 3. Verify tests pass with coverage
just test-cov
```

All checks must pass.

---

## Coding Guidelines

### Messages

```python
# Commands: imperative (intent)
@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_id: str

# Events: past tense (fact)
@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    order_id: str
    customer_id: str
```

### Type Annotations

Always use complete type hints:

```python
# Correct
def handle(self, command: CreateOrder) -> None:
    events: list[Event] = []
    order: Order = Order.create(command.order_id)

# Avoid
def handle(self, command):
    events = []
```

### Docstrings

Google-style docstrings for public APIs:

```python
def subscribe(self, message_type: type[Message], handler: Callable) -> None:
    """Subscribe a handler to a message type.

    Args:
        message_type: The message class to handle.
        handler: Callable or handler instance with handle() method.

    Example:
        >>> bus.subscribe(CreateOrder, create_order_handler)
    """
```

### Tests

Every new feature needs tests:

```python
def test_message_bus_subscription():
    """Test that handlers are called when message is published."""
    # Arrange
    bus = InMemoryMessageBus()
    events_received = []
    bus.subscribe(OrderCreated, lambda e: events_received.append(e))

    # Act
    event = OrderCreated(order_id="ORD-001")
    bus.publish(event)

    # Assert
    assert len(events_received) == 1
    assert events_received[0].order_id == "ORD-001"
```

---

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git commit -m "feat: add async message bus implementation"
```

| Type | Purpose |
|------|---------|
| `feat:` | New features |
| `fix:` | Bug fixes |
| `docs:` | Documentation |
| `test:` | Tests |
| `refactor:` | Code refactoring |
| `perf:` | Performance improvements |
| `ci:` | CI/CD changes |

---

## Pull Request Process

### 1. Create feature branch

```bash
git checkout -b feature/my-awesome-feature
```

### 2. Make changes and run quality checks

```bash
just fix && just qa
```

### 3. Push and create PR

```bash
git push origin feature/my-awesome-feature
```

Include in your PR description:

- What changed and why
- Tests added
- Breaking changes (if any)

---

## Integration Tests with Testcontainers

Integration tests for PostgreSQL and EventSourcingDB use [testcontainers-python](https://testcontainers.com/) for isolated, reproducible container-based testing.

### Container Version Management

Container image versions are defined centrally in `.container-versions.json`:

```json
{
    "postgres": "16-alpine",
    "eventsourcingdb": "latest"
}
```

Test fixtures read this file to determine which image version to use. [Dependabot](https://github.com/dependabot) monitors this file for updates.

### Updating container versions

1. Edit `.container-versions.json` with the desired image tag
2. Run tests locally to verify compatibility
3. Commit and push

---

## CI/CD Pipeline

GitHub Actions runs on every push:

- Tests on Python 3.12 and 3.13
- Tests on Linux, macOS, Windows
- Ruff linting and formatting
- Type checking with `ty`
- CodeQL security analysis

---

## Release Process

1. Update `CHANGELOG.md`
2. Tag version: `git tag v0.2.0`
3. Push tags: `git push --tags`
4. GitHub Actions publishes to PyPI

---

## Questions?

Open a [GitHub Issue](https://github.com/stefanposs/orchestrix/issues) or [Discussion](https://github.com/stefanposs/orchestrix/discussions).

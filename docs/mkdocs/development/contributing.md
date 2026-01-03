# Contributing

Beiträge zu Orchestrix sind willkommen! Hier erfährst du, wie du mitmachen kannst.

## Setup Development Environment

### 1. Repository klonen

```bash
git clone https://github.com/stefanposs/orchestrix.git
cd orchestrix
```

### 2. Development Setup

Mit `just` (empfohlen):

```bash
just setup
```

Oder manuell mit `uv`:

```bash
uv sync --all-extras --dev
```

### 3. Verify Installation

```bash
just test
```

## Development Workflow

### Available Commands

```bash
# Setup
just setup              # Initial setup
just install PKG        # Install package

# Development
just fix                # Format and auto-fix code
just qa                 # Run all quality checks
just check              # Quick check (lint + typecheck)

# Testing
just test               # Run tests
just test-cov           # Run tests with coverage
just test-watch         # Watch mode

# Build
just build              # Build package
just clean              # Clean build artifacts

# Documentation
just docs               # Serve documentation
just docs-build         # Build documentation
just docs-deploy        # Deploy to GitHub Pages

# CI/CD
just ci                 # Full CI pipeline
```

### Code Quality Standards

Wir verwenden moderne Tools für hohe Code-Qualität:

- **ruff** - Linting & Formatting (replaces black, isort, flake8, pylint)
- **mypy** - Static Type Checking (strict mode)
- **pytest** - Testing Framework
- **pytest-cov** - Code Coverage (100% required)

### Before Committing

```bash
# 1. Format code
just fix

# 2. Run quality checks
just qa

# 3. Verify tests pass
just test-cov
```

Alle Checks müssen bestehen! ✅

## Coding Guidelines

### Messages

```python
# Commands: Imperativ
@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_id: str

# Events: Vergangenheit
@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    order_id: str
    customer_id: str
```

### Type Annotations

**Immer** vollständige Type Hints verwenden:

```python
# ✅ Gut
def handle(self, command: CreateOrder) -> None:
    events: list[Event] = []
    order: Order = Order.create(command.order_id)

# ❌ Schlecht
def handle(self, command):  # No types!
    events = []
    order = Order.create(command.order_id)
```

### Docstrings

Google-style Docstrings für öffentliche APIs:

```python
def subscribe(self, message_type: type[Message], handler: Callable) -> None:
    """Subscribe a handler to a message type.
    
    Args:
        message_type: The message class to handle
        handler: Callable or handler instance with handle() method
    
    Example:
        >>> bus.subscribe(CreateOrder, create_order_handler)
    """
```

### Tests

Jede neue Funktion braucht Tests:

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

## Pull Request Process

### 1. Create Feature Branch

```bash
git checkout -b feature/my-awesome-feature
```

### 2. Make Changes

```bash
# Edit files
vim src/orchestrix/my_feature.py

# Run tests continuously
just test-watch
```

### 3. Commit Changes

Verwende [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat: add async message bus implementation"
```

Types:
- `feat:` - Neue Features
- `fix:` - Bug Fixes
- `docs:` - Dokumentation
- `test:` - Tests
- `refactor:` - Code Refactoring
- `perf:` - Performance Improvements
- `ci:` - CI/CD Changes

### 4. Run Final Checks

```bash
just ci
```

Alles muss grün sein! ✅

### 5. Push & Create PR

```bash
git push origin feature/my-awesome-feature
```

Erstelle dann einen Pull Request auf GitHub mit:

- **Beschreibung** der Änderungen
- **Warum** die Änderung notwendig ist
- **Tests** die hinzugefügt wurden
- **Breaking Changes** (falls vorhanden)

## CI/CD Pipeline

Unsere GitHub Actions Pipeline testet:

- ✅ Tests auf Python 3.9-3.13
- ✅ Tests auf Linux, macOS, Windows
- ✅ Ruff Linting
- ✅ Mypy Type Checking
- ✅ 100% Code Coverage

## Architecture Decisions

### ADR (Architecture Decision Records)

Wichtige Design-Entscheidungen werden dokumentiert:

```markdown
# ADR-001: Use Protocols instead of Abstract Base Classes

## Context
Need to define interfaces for MessageBus, EventStore, etc.

## Decision
Use typing.Protocol instead of ABC.

## Rationale
- More Pythonic (duck typing)
- Better IDE support
- No inheritance required
- Easier to mock in tests

## Consequences
Users can implement interfaces without inheriting from base classes.
```

## Community

### Communication

- **GitHub Issues** - Bug Reports & Feature Requests
- **GitHub Discussions** - Questions & Ideas
- **Pull Requests** - Code Contributions

### Code of Conduct

Sei respektvoll und konstruktiv. Siehe [CODE_OF_CONDUCT.md](https://github.com/stefanposs/orchestrix/blob/main/.github/CODE_OF_CONDUCT.md).

## Release Process

Releases werden automatisch erstellt:

1. Update `CHANGELOG.md`
2. Tag version: `git tag v0.2.0`
3. Push tags: `git push --tags`
4. GitHub Actions publisht zu PyPI

## Questions?

Erstelle ein [GitHub Issue](https://github.com/stefanposs/orchestrix/issues) oder [Discussion](https://github.com/stefanposs/orchestrix/discussions)!

## Thank You! 🎉

Jeder Beitrag ist wertvoll - egal ob Code, Dokumentation, Bug Reports oder Feedback!

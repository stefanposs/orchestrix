
# Installation

## Requirements

- **Python 3.12+**
- [uv](https://docs.astral.sh/uv/) package manager (recommended) or pip

## Install from PyPI

```bash
# With uv (recommended)
uv add orchestrix

# With pip
pip install orchestrix
```

### Optional Extras

```bash
# PostgreSQL event store
pip install orchestrix[postgres]

# Observability (Prometheus + OpenTelemetry)
pip install orchestrix[observability]

# All extras
pip install orchestrix[postgres,observability]
```

## Install from Source

```bash
git clone https://github.com/stefanposs/orchestrix.git
cd orchestrix
uv sync --all-extras --dev
```

## Verify

```python
from orchestrix.core.messaging.message import Command, Event
from orchestrix.infrastructure.memory.store import InMemoryEventStore

print("Orchestrix ready!")
```

## Next Steps

- [Quick Start](quick-start.md) — Build your first event-sourced app
- [Core Concepts](concepts.md) — Commands, Events, Aggregates

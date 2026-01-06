# Installation

## Requirements

- Python 3.9 or higher
- pip or [uv](https://docs.astral.sh/uv/) package manager

## Install from PyPI

Using pip:

```bash
pip install orchestrix
```

Using uv (recommended):

```bash
uv add orchestrix
```

## Install from Source

For development or the latest features:

```bash
git clone https://github.com/stefanposs/orchestrix.git
cd orchestrix
uv sync --all-extras --dev
```

## Verify Installation

Check that Orchestrix is installed correctly:

```python
import orchestrix

print(orchestrix.__version__)
# Output: 0.1.0
```

## Next Steps

- [Quick Start Guide](quick-start.md) - Build your first application
- [Core Concepts](concepts.md) - Understand the framework fundamentals

# Projection Demo

CQRS read model projections from event streams.

## Running

```bash
uv run python -m bases.orchestrix.projection_demo.demo_projection
```

## Architecture
All logic lives in `bases/orchestrix/projection_demo/`. This project assembly is a thin deployment wrapper following the Polylith pattern.

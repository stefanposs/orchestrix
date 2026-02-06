# Tracing Demo

Distributed tracing with OpenTelemetry and Jaeger integration.

## Running

```bash
uv run python -m bases.orchestrix.tracing_demo.demo_tracing
```

## Architecture
All logic lives in `bases/orchestrix/`. This project assembly is a thin deployment wrapper following the Polylith pattern.

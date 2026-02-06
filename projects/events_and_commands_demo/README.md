# Events & Commands Demo

Minimal demo of command/event separation — the foundational pattern in Orchestrix.

## Running

```bash
uv run python -m bases.orchestrix.events_and_commands_demo.demo_events_and_commands
```

## Architecture
All logic lives in `bases/orchestrix/events_and_commands_demo/`. This project assembly is a thin deployment wrapper following the Polylith pattern.

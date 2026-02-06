# Web GUI Demo

Interactive dashboard for exploring Orchestrix event sourcing in real time — built with Dash and the `ox-*` design system.

## What It Demonstrates
- **Dashboard**: Live KPI cards, event timeline chart, recent error list
- **Event Explorer**: Search, filter, and inspect stored domain events
- **Command Center**: Send commands, view schemas, track execution results
- **Aggregate Viewer**: Browse aggregate state and event history timeline

## Running

```bash
uv run python -m bases.orchestrix.web_gui_demo.app
```

Open **http://localhost:8050** in your browser.

## Key Files
| File | Purpose |
|------|---------|
| `bases/orchestrix/web_gui_demo/app.py` | Dash app entry point with routing |
| `bases/orchestrix/web_gui_demo/pages/` | Dashboard, Event Explorer, Command Center, Aggregate Viewer |
| `bases/orchestrix/web_gui_demo/components/` | Sidebar, KPI cards, error list |
| `bases/orchestrix/web_gui_demo/services/` | Data service (EventStore + MessageBus wrapper) |
| `bases/orchestrix/web_gui_demo/assets/` | CSS design system (`dashboard_theme.css`) |

## Architecture
All UI logic lives in `bases/orchestrix/web_gui_demo/`. This project assembly is a thin deployment wrapper following the Polylith pattern.

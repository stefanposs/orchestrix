# Orchestrix Web GUI - Enterprise-Ready Dash Application

Enterprise-ready, user-friendly web GUI for the Orchestrix event-sourcing framework built with Dash and Python.

## Features

### 🎯 Core Capabilities
- **Dashboard**: Real-time system overview with KPIs, live metrics charts, and error monitoring
- **Event Explorer**: Browse and filter events across all aggregates with advanced search
- **Aggregate Viewer**: Inspect aggregates, view event history, and time-travel through versions
- **Command Center**: Dispatch commands with dynamic forms and batch JSON processing

### 🎨 Design & UX
- **Modern UI**: Professional design system with consistent styling
- **Responsive Layout**: Works seamlessly on desktop and mobile devices
- **Real-time Updates**: Live data refresh with configurable intervals
- **User Feedback**: Clear success/error messages and loading states

### 🏗️ Architecture
- **Service Layer**: Clean separation with `DataService` for data access
- **Component-Based**: Reusable UI components with proper encapsulation
- **Extensible**: Easy to add new pages, commands, and features
- **Type-Safe**: Full type hints throughout the codebase

## Installation

Using `uv` (recommended):

```bash
# Install dependencies
uv sync

# Run the application
uv run python bases/orchestrix/web_gui_demo/app.py
```

Or with pip:

```bash
pip install -e bases/orchestrix/web_gui_demo
python bases/orchestrix/web_gui_demo/app.py
```

## Usage

1. Start the application - it will be available at `http://localhost:8050`
2. Navigate through the sidebar:
   - **Dashboard**: System overview and metrics
   - **Event Explorer**: Browse and filter events
   - **Aggregate Viewer**: Inspect aggregates and their history
   - **Command Center**: Dispatch commands to the system

## Architecture

### Service Layer
The `DataService` class provides a clean interface for:
- Querying events from the event store
- Loading aggregate summaries
- Dispatching commands via the message bus
- Getting system statistics

### Component Structure
```
bases/orchestrix/web_gui_demo/
├── app.py                 # Main Dash application
├── services/              # Business logic layer
│   └── data_service.py
├── components/            # Reusable UI components
│   ├── sidebar.py
│   ├── kpi_cards.py
│   ├── dashboard_chart.py
│   └── dashboard_error_list.py
├── pages/                 # Page components
│   ├── dashboard.py
│   ├── event_explorer.py
│   ├── aggregate_viewer.py
│   └── command_center.py
└── assets/                # Static assets
    └── dashboard_theme.css
```

## Extending the GUI

### Adding a New Page

1. Create a new file in `pages/`:
```python
from dash import html

def my_new_page():
    return html.Div([
        html.H1("My New Page"),
        # Your content here
    ])
```

2. Register it in `pages/__init__.py`:
```python
PAGES["/my-page"] = my_new_page
```

### Adding Command Schemas

Update `SAMPLE_COMMANDS` in `pages/command_center.py`:

```python
SAMPLE_COMMANDS.append({
    "name": "MyNewCommand",
    "description": "Description of the command",
    "fields": [
        {"name": "field1", "label": "Field 1", "type": "text", "required": True},
    ]
})
```

## Development

### Code Quality
- Type hints throughout
- Follows PEP 8 style guide
- Uses `ruff` for linting
- Uses `black` for formatting

### Testing
```bash
pytest bases/orchestrix/web_gui_demo/
```

## Requirements

- Python >= 3.12
- Dash >= 3.3.0
- Dash Bootstrap Components >= 2.0.4
- Plotly >= 6.5.1
- Orchestrix core library

## License

MIT License - see LICENSE file for details

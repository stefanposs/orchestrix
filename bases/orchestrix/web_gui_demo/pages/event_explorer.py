"""Event Explorer page for viewing and filtering events."""

from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import dash_table
from datetime import datetime


def event_explorer_page():
    """Create the event explorer page.

    Returns:
        Event explorer layout component
    """
    layout = html.Div([
        dcc.Interval(id="event-explorer-interval", interval=3*1000, n_intervals=0),
        dcc.Store(id="event-explorer-store", data={"events": []}),
        html.Div([
            html.H1("Event Explorer", className="dashboard-header"),
            html.P("Browse and filter events from the event store", className="page-subtitle"),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5("Filters", className="mb-3"),
                        dbc.Label("Event Type", className="mb-2"),
                        dcc.Dropdown(
                            id="event-type-filter",
                            placeholder="All event types",
                            clearable=True,
                            className="mb-3"
                        ),
                        dbc.Label("Aggregate ID", className="mb-2"),
                        dcc.Dropdown(
                            id="aggregate-id-filter",
                            placeholder="All aggregates",
                            clearable=True,
                            className="mb-3"
                        ),
                        dbc.Button([
                            html.I(className="bi bi-arrow-clockwise me-2"),
                            "Refresh"
                        ], id="refresh-events-btn", color="primary", className="w-100 mb-2"),
                        dbc.Button([
                            html.I(className="bi bi-lightning me-2"),
                            "Jetzt Events laden"
                        ], id="load-events-now-btn", color="secondary", className="w-100"),
                    ])
                ], className="shadow-hover")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H5("Events", className="mb-0"),
                            html.Span(id="event-count-badge", className="badge bg-primary ms-2")
                        ], className="d-flex align-items-center mb-3"),
                        dbc.InputGroup([
                            dbc.InputGroupText([
                                html.I(className="bi bi-search")
                            ]),
                            dbc.Input(
                                id="event-search-input",
                                placeholder="Search events by type, aggregate ID, or event ID...",
                                type="text",
                                className="mb-3"
                            ),
                        ], className="mb-3"),
                        html.Div(id="event-table-container"),
                    ])
                ], className="shadow-hover")
            ], width=9),
        ], className="g-4"),
    ], className="container-fluid")

    return layout


# Register callbacks at module level
@callback(
    Output("event-explorer-store", "data"),
    Output("event-type-filter", "options"),
    Output("aggregate-id-filter", "options"),
    Input("event-explorer-interval", "n_intervals"),
    Input("refresh-events-btn", "n_clicks"),
    Input("load-events-now-btn", "n_clicks"),
    prevent_initial_call=False
)
def load_events(n_interval: int, n_refresh: int, n_load_now: int) -> tuple:
        """Load events from data service.

        Args:
            n_interval: Interval counter
            n_refresh: Refresh button clicks

        Returns:
            Tuple of (events_data, event_type_options, aggregate_id_options)
        """
        import dash
        data_service = dash.get_app().data_service  # type: ignore[attr-defined]
        
        events = data_service.get_all_events(limit=500)
        
        # Extract unique event types and aggregate IDs
        event_types = sorted(set(e.get("type", "Unknown") for e in events))
        aggregate_ids = sorted(set(e.get("aggregate_id", "Unknown") for e in events))
        
        return (
            {"events": events},
            [{"label": et, "value": et} for et in event_types],
            [{"label": aid, "value": aid} for aid in aggregate_ids],
        )


@callback(
    Output("event-table-container", "children"),
    Output("event-count-badge", "children"),
    Input("event-explorer-store", "data"),
    Input("event-type-filter", "value"),
    Input("aggregate-id-filter", "value"),
    Input("event-search-input", "value"),
)
def filter_events(
    store_data: dict,
    event_type: str | None,
    aggregate_id: str | None,
    search_text: str | None,
) -> tuple:
    """Filter and display events.

    Args:
        store_data: Stored events data
        event_type: Selected event type filter
        aggregate_id: Selected aggregate ID filter
        search_text: Search text input

    Returns:
        Tuple of (table_component, count_badge)
    """
    import dash
    events = store_data.get("events", [])

    # Apply filters
    filtered_events = events
    if event_type:
        filtered_events = [e for e in filtered_events if e.get("type") == event_type]
    if aggregate_id:
        filtered_events = [e for e in filtered_events if e.get("aggregate_id") == aggregate_id]
    if search_text:
        search_lower = search_text.lower()
        filtered_events = [
            e for e in filtered_events
            if search_lower in str(e.get("type", "")).lower()
            or search_lower in str(e.get("aggregate_id", "")).lower()
            or search_lower in str(e.get("id", "")).lower()
        ]

    if not filtered_events:
        return (
            html.Div([
                html.I(className="bi bi-inbox me-2", style={"fontSize": "2rem"}),
                html.P("No events found", className="mt-2 mb-0"),
                html.Small(
                    "Try adjusting your filters or wait for new events",
                    className="text-muted"
                )
            ], className="text-center py-5"),
            "0"
        )

    # Prepare data for DataTable
    table_data = []
    for event in filtered_events[-500:]:  # Show last 500
        event_id = event.get("id", "N/A")
        event_type_val = event.get("type", "Unknown")
        timestamp = event.get("timestamp", "N/A")
        agg_id = event.get("aggregate_id", "N/A")

        # Format timestamp
        if "T" in timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                formatted_time = timestamp[:19] if len(timestamp) > 19 else timestamp
        else:
            formatted_time = timestamp[:19] if len(timestamp) > 19 else timestamp

        table_data.append({
            "Timestamp": formatted_time,
            "Type": event_type_val,
            "Aggregate ID": agg_id,
            "Event ID": event_id[:16] + "..." if len(event_id) > 16 else event_id,
            "Full Event ID": event_id,  # Hidden column for reference
        })

    # Define columns
    columns = [
        {"name": "Timestamp", "id": "Timestamp", "type": "datetime"},
        {
            "name": "Type",
            "id": "Type",
            "presentation": "markdown",
            "type": "text",
        },
        {"name": "Aggregate ID", "id": "Aggregate ID", "type": "text"},
        {"name": "Event ID", "id": "Event ID", "type": "text"},
        {"name": "Full Event ID", "id": "Full Event ID", "hideable": True},
    ]

    # Format Type column with badges
    for row in table_data:
        row["Type"] = f"`{row['Type']}`"

    table = dash_table.DataTable(
        id="event-data-table",
        columns=columns,
        data=table_data,
        page_size=20,
        page_action="native",
        sort_action="native",
        filter_action="native",
        style_table={
            "overflowX": "auto",
            "borderRadius": "0.5rem",
        },
        style_header={
            "backgroundColor": "#1976d2",
            "color": "white",
            "fontWeight": "bold",
            "textAlign": "left",
            "padding": "12px",
            "border": "none",
        },
        style_cell={
            "textAlign": "left",
            "padding": "10px",
            "fontFamily": "Inter, sans-serif",
            "fontSize": "0.875rem",
            "border": "1px solid #e8eaf6",
        },
        style_data={
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "#f8f9fa",
            },
            {
                "if": {"filter_query": "{Type} contains OrderCreated"},
                "backgroundColor": "#e8f5e9",
            },
            {
                "if": {"filter_query": "{Type} contains OrderCancelled"},
                "backgroundColor": "#ffebee",
            },
        ],
        css=[
            {
                "selector": ".dash-table-tooltip",
                "rule": "font-family: Inter, sans-serif",
            },
        ],
    )

    return html.Div([
        table
    ], className="event-table-wrapper"), str(len(filtered_events))


## Duplicate callback for event-table-container and event-count-badge removed

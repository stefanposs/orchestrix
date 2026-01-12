"""Aggregate Viewer page for browsing aggregates."""

from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import dash_table
import json


def aggregate_viewer_page():
    """Create the aggregate viewer page.

    Returns:
        Aggregate viewer layout component
    """
    layout = html.Div([
        dcc.Interval(id="aggregate-viewer-interval", interval=3*1000, n_intervals=0),
        dcc.Store(id="aggregate-viewer-store", data={"aggregates": []}),
        html.Div([
            html.H1("Aggregate Viewer", className="dashboard-header"),
            html.P("Browse aggregates and view their event history", className="page-subtitle"),
        ], className="mb-4"),
        dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H5("Aggregates", className="mb-0"),
                    html.Span(id="aggregate-count-badge", className="badge bg-primary ms-2")
                ], className="d-flex align-items-center mb-3"),
                dbc.InputGroup([
                    dbc.InputGroupText([
                        html.I(className="bi bi-search", style={"fontSize": "1rem"})
                    ]),
                    dbc.Input(
                        id="aggregate-search-input",
                        placeholder="Search aggregates by ID or event type...",
                        type="text",
                        className="mb-3"
                    ),
                ], className="mb-3"),
                html.Div(id="aggregate-table-container"),
            ])
        ], className="shadow-hover"),
    ], className="container-fluid")

    return layout


# Register callbacks at module level
@callback(
    Output("aggregate-viewer-store", "data"),
    Output("aggregate-count-badge", "children"),
    Input("aggregate-viewer-interval", "n_intervals"),
    prevent_initial_call=False
)
def load_aggregates(n: int) -> tuple:
        """Load aggregates from data service.

        Args:
            n: Interval counter

        Returns:
            Tuple of (aggregates_data, count_badge)
        """
        import dash
        data_service = dash.get_app().data_service  # type: ignore[attr-defined]
        
        aggregates = data_service.get_all_aggregates_summary()
        
        return {"aggregates": aggregates}, str(len(aggregates))


@callback(
    Output("aggregate-table-container", "children"),
    Input("aggregate-viewer-store", "data"),
    Input("aggregate-search-input", "value"),
)
def render_aggregate_table(store_data: dict, search_text: str | None) -> html.Div:
        """Render aggregate table.

        Args:
            store_data: Stored aggregates data
            search_text: Search text input

        Returns:
            Table component
        """
        aggregates = store_data.get("aggregates", [])
        
        # Apply search filter
        if search_text:
            search_lower = search_text.lower()
            aggregates = [
                agg for agg in aggregates
                if search_lower in str(agg.get("id", "")).lower()
                or search_lower in str(agg.get("first_event", {}).get("type", "")).lower()
                or search_lower in str(agg.get("last_event", {}).get("type", "")).lower()
            ]
        
        if not aggregates:
            return html.Div([
                html.I(className="bi bi-inbox me-2", style={"fontSize": "2rem"}),
                html.P("No aggregates found", className="mt-2 mb-0"),
                html.Small("Try adjusting your search or wait for new aggregates", className="text-muted")
            ], className="text-center py-5")
        
        # Prepare data for DataTable
        table_data = []
        for agg in aggregates:
            agg_id = agg.get("id", "N/A")
            event_count = agg.get("event_count", 0)
            version = agg.get("version", 0)
            first_event = agg.get("first_event", {})
            last_event = agg.get("last_event", {})
            
            first_event_type = first_event.get("type", "N/A") if first_event else "N/A"
            last_event_type = last_event.get("type", "N/A") if last_event else "N/A"
            
            table_data.append({
                "Aggregate ID": agg_id,
                "Events": event_count,
                "Version": f"v{version}",
                "First Event": first_event_type,
                "Last Event": last_event_type,
                "Actions": agg_id,  # For button reference
            })
        
        # Define columns
        columns = [
            {"name": "Aggregate ID", "id": "Aggregate ID", "type": "text"},
            {"name": "Events", "id": "Events", "type": "numeric"},
            {"name": "Version", "id": "Version", "type": "text"},
            {"name": "First Event", "id": "First Event", "type": "text"},
            {"name": "Last Event", "id": "Last Event", "type": "text"},
            {"name": "Actions", "id": "Actions", "presentation": "markdown", "type": "text"},
        ]
        
        # Format Actions column with buttons
        for row in table_data:
            agg_id = row["Actions"]
            row["Actions"] = f"[Details](/aggregates/{agg_id})"
        
        table = dash_table.DataTable(
            id="aggregate-data-table",
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
                    "if": {"filter_query": "{Events} > 5"},
                    "backgroundColor": "#e8f5e9",
                },
            ],
        )
        
        return html.Div([table], className="aggregate-table-wrapper")

def aggregate_details_page(aggregate_id: str) -> html.Div:
    """Create aggregate details page.

    Args:
        aggregate_id: The aggregate ID to display

    Returns:
        Aggregate details layout component
    """
    import dash
    
    try:
        data_service = dash.get_app().data_service  # type: ignore[attr-defined]
        events = data_service.get_events_for_aggregate(aggregate_id)
        summary = data_service.get_aggregate_summary(aggregate_id)
    except Exception:
        return html.Div([
            html.H3("Aggregate not found", className="text-danger"),
            html.P(f"Aggregate ID: {aggregate_id}")
        ], className="p-4")
    
    if not summary:
        return html.Div([
            html.H3("Aggregate not found", className="text-danger"),
            html.P(f"Aggregate ID: {aggregate_id}")
        ], className="p-4")
    
    # Summary card
    summary_card = dbc.Card([
        dbc.CardBody([
            html.H4(f"Aggregate: {aggregate_id}", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    html.Small("Total Events", className="text-muted d-block"),
                    html.H5(str(summary.get("event_count", 0)), className="mb-0")
                ]),
                dbc.Col([
                    html.Small("Version", className="text-muted d-block"),
                    html.H5(f"v{summary.get('version', 0)}", className="mb-0")
                ]),
            ])
        ])
    ], className="mb-4 shadow-hover")
    
    # Events table
    if events:
        events_header = html.Thead(html.Tr([
            html.Th("#"),
            html.Th("Event ID"),
            html.Th("Type"),
            html.Th("Timestamp"),
            html.Th("Data"),
        ]))
        events_rows = []
        for idx, event in enumerate(events, 1):
            event_id = event.get("id", "N/A")
            event_type = event.get("type", "Unknown")
            timestamp = event.get("timestamp", "N/A")
            data_str = event.get("data", "{}")
            # Format timestamp
            if "T" in timestamp:
                date_part, time_part = timestamp.split("T")
                formatted_time = f"{date_part} {time_part[:8]}"
            else:
                formatted_time = timestamp[:19]
            events_rows.append(
                html.Tr([
                    html.Td(html.Small(str(idx), className="text-muted")),
                    html.Td(html.Code(event_id[:12] + "...", className="text-primary")),
                    html.Td([
                        html.Span(event_type, className="badge bg-primary")
                    ]),
                    html.Td(html.Small(formatted_time, className="text-muted")),
                    html.Td([
                        dbc.Button(
                            html.I(className="bi bi-code"),
                            size="sm",
                            color="info",
                            id={"type": "view-event-data", "index": event_id},
                        )
                    ]),
                ])
            )
        events_table = dbc.Table([
            events_header,
            html.Tbody(events_rows)
        ], bordered=True, hover=True, responsive=True, striped=True, className="table-card")
    else:
        events_table = html.Div("No events found", className="text-center text-muted py-4")

    return html.Div([
        dbc.Button([
            html.I(className="bi bi-arrow-left me-2"),
            "Back to Aggregates"
        ], href="/aggregates", color="secondary", className="mb-3"),
        summary_card,
        html.H5("Event History", className="mb-3"),
        events_table,
    ], className="container-fluid p-4")

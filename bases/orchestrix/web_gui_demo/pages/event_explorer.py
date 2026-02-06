"""Event Explorer – browse & filter events from the store."""

from datetime import datetime

import dash_table
from dash import Input, Output, callback, dcc, html


def event_explorer_page() -> html.Div:
    """Create the event explorer page layout."""
    return html.Div(
        [
            dcc.Interval(id="event-explorer-interval", interval=3_000, n_intervals=0),
            dcc.Store(id="event-explorer-store", data={"events": []}),
            # Header
            html.Div(
                [
                    html.H1("Event Explorer", className="ox-page-title"),
                    html.P(
                        "Browse and filter events from the event store",
                        className="ox-page-subtitle",
                    ),
                ],
                className="ox-page-header",
            ),
            # Body: filter sidebar + table
            html.Div(
                [
                    # --- Filters ---
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H3(
                                        [
                                            html.I(className="bi bi-funnel me-2"),
                                            "Filters",
                                        ],
                                        className="ox-card-title",
                                    ),
                                ],
                                className="ox-card-header",
                            ),
                            html.Div(
                                [
                                    html.Label("Event Type", className="ox-label"),
                                    dcc.Dropdown(
                                        id="event-type-filter",
                                        placeholder="All event types",
                                        clearable=True,
                                        className="ox-dropdown",
                                    ),
                                    html.Label(
                                        "Aggregate ID",
                                        className="ox-label",
                                        style={"marginTop": "1rem"},
                                    ),
                                    dcc.Dropdown(
                                        id="aggregate-id-filter",
                                        placeholder="All aggregates",
                                        clearable=True,
                                        className="ox-dropdown",
                                    ),
                                    html.Button(
                                        [html.I(className="bi bi-arrow-clockwise me-1"), "Refresh"],
                                        id="refresh-events-btn",
                                        n_clicks=0,
                                        className="ox-btn ox-btn-primary",
                                        style={"width": "100%", "marginTop": "1.5rem"},
                                    ),
                                    html.Button(
                                        [html.I(className="bi bi-lightning me-1"), "Load Now"],
                                        id="load-events-now-btn",
                                        n_clicks=0,
                                        className="ox-btn ox-btn-secondary",
                                        style={"width": "100%", "marginTop": ".5rem"},
                                    ),
                                ],
                                className="ox-card-body",
                            ),
                        ],
                        className="ox-card",
                        style={"flex": "0 0 280px"},
                    ),
                    # --- Table ---
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.H3("Events", className="ox-card-title"),
                                            html.Span(
                                                id="event-count-badge",
                                                className="ox-badge ox-badge-primary",
                                                style={"marginLeft": ".5rem"},
                                            ),
                                        ],
                                        style={"display": "flex", "alignItems": "center"},
                                    ),
                                    dcc.Input(
                                        id="event-search-input",
                                        placeholder=("Search by type, aggregate or event ID\u2026"),
                                        type="text",
                                        className="ox-input",
                                        style={"width": "100%", "marginTop": ".75rem"},
                                    ),
                                ],
                                className="ox-card-header",
                            ),
                            html.Div(id="event-table-container", className="ox-card-body"),
                        ],
                        className="ox-card",
                        style={"flex": "1 1 0%", "minWidth": 0},
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "1.5rem",
                    "alignItems": "flex-start",
                },
            ),
        ],
        className="ox-animate-in",
    )


# ── Callbacks (module-level, Dash auto-discovers) ───────────────────


@callback(
    Output("event-explorer-store", "data"),
    Output("event-type-filter", "options"),
    Output("aggregate-id-filter", "options"),
    Input("event-explorer-interval", "n_intervals"),
    Input("refresh-events-btn", "n_clicks"),
    Input("load-events-now-btn", "n_clicks"),
    prevent_initial_call=False,
)
def load_events(n_interval: int, n_refresh: int, n_load_now: int) -> tuple:
    """Fetch events and unique filter values from the data service."""
    import dash

    ds = dash.get_app().data_service
    events = ds.get_all_events(limit=500)

    event_types = sorted({e.get("type", "Unknown") for e in events})
    aggregate_ids = sorted({e.get("aggregate_id", "Unknown") for e in events})

    return (
        {"events": events},
        [{"label": t, "value": t} for t in event_types],
        [{"label": a, "value": a} for a in aggregate_ids],
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
    """Apply filters and render the events DataTable."""
    events = store_data.get("events", [])

    filtered = events
    if event_type:
        filtered = [e for e in filtered if e.get("type") == event_type]
    if aggregate_id:
        filtered = [e for e in filtered if e.get("aggregate_id") == aggregate_id]
    if search_text:
        q = search_text.lower()
        filtered = [
            e
            for e in filtered
            if q in str(e.get("type", "")).lower()
            or q in str(e.get("aggregate_id", "")).lower()
            or q in str(e.get("id", "")).lower()
        ]

    if not filtered:
        return (
            html.Div(
                [
                    html.I(className="bi bi-inbox", style={"fontSize": "2rem", "opacity": ".4"}),
                    html.P("No events found", style={"margin": ".5rem 0 0"}),
                    html.Small("Adjust filters or wait for new events"),
                ],
                className="ox-empty",
            ),
            "0",
        )

    # Build table rows
    table_data = []
    for ev in filtered[-500:]:
        eid = ev.get("id", "N/A")
        ts = ev.get("timestamp", "N/A")
        if "T" in ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts = dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                ts = ts[:19]
        else:
            ts = ts[:19]

        table_data.append(
            {
                "Timestamp": ts,
                "Type": f"`{ev.get('type', 'Unknown')}`",
                "Aggregate ID": ev.get("aggregate_id", "N/A"),
                "Event ID": eid[:16] + "\u2026" if len(eid) > 16 else eid,
                "Full Event ID": eid,
            }
        )

    columns = [
        {"name": "Timestamp", "id": "Timestamp", "type": "datetime"},
        {"name": "Type", "id": "Type", "presentation": "markdown", "type": "text"},
        {"name": "Aggregate ID", "id": "Aggregate ID", "type": "text"},
        {"name": "Event ID", "id": "Event ID", "type": "text"},
        {"name": "Full Event ID", "id": "Full Event ID", "hideable": True},
    ]

    table = dash_table.DataTable(
        id="event-data-table",
        columns=columns,
        data=table_data,
        page_size=20,
        page_action="native",
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto", "borderRadius": "var(--ox-radius)"},
        style_header={
            "backgroundColor": "var(--ox-bg-subtle)",
            "color": "var(--ox-text-secondary)",
            "fontWeight": "600",
            "textAlign": "left",
            "padding": "10px 14px",
            "border": "none",
            "fontSize": ".78rem",
            "textTransform": "uppercase",
            "letterSpacing": ".04em",
            "borderBottom": "2px solid var(--ox-border)",
        },
        style_cell={
            "textAlign": "left",
            "padding": "10px 14px",
            "fontFamily": "Inter, sans-serif",
            "fontSize": ".85rem",
            "border": "none",
            "borderBottom": "1px solid var(--ox-border-light)",
        },
        style_data={"whiteSpace": "normal", "height": "auto"},
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "var(--ox-bg-subtle)",
            },
            {
                "if": {"filter_query": "{Type} contains OrderCreated"},
                "backgroundColor": "#ecfdf5",
            },
            {
                "if": {"filter_query": "{Type} contains OrderCancelled"},
                "backgroundColor": "#fef2f2",
            },
        ],
    )

    return html.Div(table, className="ox-table-wrap"), str(len(filtered))

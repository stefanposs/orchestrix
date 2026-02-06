"""Aggregate Viewer – browse aggregates and their event history."""

import dash_table
from dash import Input, Output, callback, dcc, html


def aggregate_viewer_page() -> html.Div:
    """Create the aggregate viewer page layout."""
    return html.Div(
        [
            dcc.Interval(id="aggregate-viewer-interval", interval=3_000, n_intervals=0),
            dcc.Store(id="aggregate-viewer-store", data={"aggregates": []}),
            # Header
            html.Div(
                [
                    html.H1("Aggregate Viewer", className="ox-page-title"),
                    html.P(
                        "Browse aggregates and view their event history",
                        className="ox-page-subtitle",
                    ),
                ],
                className="ox-page-header",
            ),
            # Main card
            html.Div(
                [
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.H3("Aggregates", className="ox-card-title"),
                                    html.Span(
                                        id="aggregate-count-badge",
                                        className="ox-badge ox-badge-primary",
                                        style={"marginLeft": ".5rem"},
                                    ),
                                ],
                                style={"display": "flex", "alignItems": "center"},
                            ),
                            dcc.Input(
                                id="aggregate-search-input",
                                placeholder="Search by ID or event type\u2026",
                                type="text",
                                className="ox-input",
                                style={"width": "100%", "marginTop": ".75rem"},
                            ),
                        ],
                        className="ox-card-header",
                    ),
                    html.Div(id="aggregate-table-container", className="ox-card-body"),
                ],
                className="ox-card",
            ),
        ],
        className="ox-animate-in",
    )


# ── Callbacks ────────────────────────────────────────────────────────


@callback(
    Output("aggregate-viewer-store", "data"),
    Output("aggregate-count-badge", "children"),
    Input("aggregate-viewer-interval", "n_intervals"),
    prevent_initial_call=False,
)
def load_aggregates(n: int) -> tuple:
    """Fetch aggregate summaries from the data service."""
    import dash

    ds = dash.get_app().data_service
    aggregates = ds.get_all_aggregates_summary()
    return {"aggregates": aggregates}, str(len(aggregates))


@callback(
    Output("aggregate-table-container", "children"),
    Input("aggregate-viewer-store", "data"),
    Input("aggregate-search-input", "value"),
)
def render_aggregate_table(store_data: dict, search_text: str | None) -> html.Div:
    """Render the aggregates DataTable with optional search filter."""
    aggregates = store_data.get("aggregates", [])

    if search_text:
        q = search_text.lower()
        aggregates = [
            a
            for a in aggregates
            if q in str(a.get("id", "")).lower()
            or q in str(a.get("first_event", {}).get("type", "")).lower()
            or q in str(a.get("last_event", {}).get("type", "")).lower()
        ]

    if not aggregates:
        return html.Div(
            [
                html.I(className="bi bi-inbox", style={"fontSize": "2rem", "opacity": ".4"}),
                html.P("No aggregates found"),
            ],
            className="ox-empty",
        )

    table_data = []
    for a in aggregates:
        aid = a.get("id", "N/A")
        first_ev = (a.get("first_event") or {}).get("type", "N/A")
        last_ev = (a.get("last_event") or {}).get("type", "N/A")
        table_data.append(
            {
                "Aggregate ID": aid,
                "Events": a.get("event_count", 0),
                "Version": f"v{a.get('version', 0)}",
                "First Event": first_ev,
                "Last Event": last_ev,
                "Actions": f"[Details](/aggregates/{aid})",
            }
        )

    table = dash_table.DataTable(
        id="aggregate-data-table",
        columns=[
            {"name": "Aggregate ID", "id": "Aggregate ID"},
            {"name": "Events", "id": "Events", "type": "numeric"},
            {"name": "Version", "id": "Version"},
            {"name": "First Event", "id": "First Event"},
            {"name": "Last Event", "id": "Last Event"},
            {"name": "Actions", "id": "Actions", "presentation": "markdown"},
        ],
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
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "var(--ox-bg-subtle)"},
            {"if": {"filter_query": "{Events} > 5"}, "backgroundColor": "#ecfdf5"},
        ],
    )

    return html.Div(table, className="ox-table-wrap")


def aggregate_details_page(aggregate_id: str) -> html.Div:
    """Render the detail page for a single aggregate with its event timeline."""
    import dash

    try:
        ds = dash.get_app().data_service
        events = ds.get_events_for_aggregate(aggregate_id)
        summary = ds.get_aggregate_summary(aggregate_id)
    except Exception:
        return html.Div(
            [
                html.H3("Aggregate not found", style={"color": "var(--ox-danger)"}),
                html.P(f"Aggregate ID: {aggregate_id}"),
            ],
            style={"padding": "2rem"},
        )

    if not summary:
        return html.Div(
            [
                html.H3("Aggregate not found", style={"color": "var(--ox-danger)"}),
                html.P(f"Aggregate ID: {aggregate_id}"),
            ],
            style={"padding": "2rem"},
        )

    # Summary card
    summary_card = html.Div(
        [
            html.Div(
                html.H3(f"Aggregate: {aggregate_id}", className="ox-card-title"),
                className="ox-card-header",
            ),
            html.Div(
                html.Div(
                    [
                        html.Div(
                            [
                                html.Small("Total Events", style={"opacity": ".6"}),
                                html.H4(str(summary.get("event_count", 0))),
                            ]
                        ),
                        html.Div(
                            [
                                html.Small("Version", style={"opacity": ".6"}),
                                html.H4(f"v{summary.get('version', 0)}"),
                            ]
                        ),
                    ],
                    style={"display": "flex", "gap": "3rem"},
                ),
                className="ox-card-body",
            ),
        ],
        className="ox-card",
    )

    # Event timeline
    if events:
        rows = []
        for idx, ev in enumerate(events, 1):
            eid = ev.get("id", "N/A")
            ts = ev.get("timestamp", "N/A")
            if "T" in ts:
                d, t = ts.split("T")
                ts = f"{d} {t[:8]}"
            else:
                ts = ts[:19]
            rows.append(
                html.Tr(
                    [
                        html.Td(str(idx), style={"opacity": ".5"}),
                        html.Td(
                            html.Code(eid[:12] + "\u2026" if len(eid) > 12 else eid),
                            style={"color": "var(--ox-primary)"},
                        ),
                        html.Td(
                            html.Span(
                                ev.get("type", "?"),
                                className="ox-badge ox-badge-primary",
                            )
                        ),
                        html.Td(ts, style={"opacity": ".6", "fontSize": ".85rem"}),
                    ]
                )
            )
        events_table = html.Table(
            [
                html.Thead(
                    html.Tr(
                        [html.Th("#"), html.Th("Event ID"), html.Th("Type"), html.Th("Timestamp")]
                    )
                ),
                html.Tbody(rows),
            ],
            className="ox-table",
        )
    else:
        events_table = html.Div("No events found", className="ox-empty")

    return html.Div(
        [
            html.A(
                [html.I(className="bi bi-arrow-left"), " Back to Aggregates"],
                href="/aggregates",
                className="ox-btn ox-btn-secondary",
                style={"display": "inline-block", "marginBottom": "1rem", "textDecoration": "none"},
            ),
            summary_card,
            html.Div(
                [
                    html.Div(
                        html.H3("Event History", className="ox-card-title"),
                        className="ox-card-header",
                    ),
                    html.Div(events_table, className="ox-card-body"),
                ],
                className="ox-card",
                style={"marginTop": "1.5rem"},
            ),
        ],
    )

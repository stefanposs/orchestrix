"""Dashboard page – real-time KPIs, live chart & error feed."""

import datetime

import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html

from ..components.dashboard_error_list import dashboard_error_list
from ..components.kpi_cards import kpi_cards

# ── Plotly figure factory ────────────────────────────────────────────

_TRACE_COLORS = {
    "Events": "#4f46e5",
    "Commands": "#3b82f6",
    "Errors": "#ef4444",
}


def _empty_figure() -> go.Figure:
    """Return an empty 3-trace figure matching the design system."""
    fig = go.Figure()
    for name, color in _TRACE_COLORS.items():
        fig.add_trace(
            go.Scatter(
                x=[],
                y=[],
                mode="lines",
                name=name,
                line={"color": color, "width": 2.5, "shape": "spline"},
                fill="tozeroy",
                fillcolor=color.replace(")", ", 0.06)").replace("rgb", "rgba")
                if color.startswith("rgb")
                else color + "0f",
            )
        )
    fig.update_layout(
        margin={"t": 20, "b": 40, "l": 50, "r": 20},
        height=320,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "bgcolor": "rgba(255,255,255,.0)",
            "font": {"size": 12},
        },
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font={"size": 12, "family": "Inter, sans-serif", "color": "#64748b"},
        hovermode="x unified",
        xaxis={
            "showgrid": False,
            "zeroline": False,
            "showline": True,
            "linecolor": "#e2e8f0",
        },
        yaxis={
            "showgrid": True,
            "gridcolor": "#f1f5f9",
            "zeroline": False,
            "rangemode": "tozero",
        },
    )
    return fig


# ── Page layout ──────────────────────────────────────────────────────


def dashboard_page() -> html.Div:
    """Create the main dashboard page layout."""
    return html.Div(
        [
            dcc.Interval(id="dashboard-interval", interval=2_000, n_intervals=0),
            dcc.Store(
                id="dashboard-state-store",
                data={
                    "event_history": [],
                    "command_history": [],
                    "error_history": [],
                },
            ),
            # Header
            html.Div(
                [
                    html.H1("System Dashboard", className="ox-page-title"),
                    html.P(
                        "Real-time event-sourcing metrics and monitoring",
                        className="ox-page-subtitle",
                    ),
                ],
                className="ox-page-header",
            ),
            # KPIs
            html.Div(id="kpi-cards-container"),
            # Chart card
            html.Div(
                [
                    html.Div(
                        [
                            html.H3(
                                [html.I(className="bi bi-graph-up me-2"), "Live Metrics"],
                                className="ox-card-title",
                            ),
                            html.Span(
                                "Last 60 data points",
                                style={
                                    "fontSize": ".75rem",
                                    "color": "var(--ox-text-muted)",
                                },
                            ),
                        ],
                        className="ox-card-header",
                    ),
                    html.Div(
                        dcc.Graph(
                            id="dashboard-metrics-graph",
                            figure=_empty_figure(),
                            config={
                                "displayModeBar": False,
                                "displaylogo": False,
                            },
                            animate=True,
                            style={"borderRadius": "0 0 var(--ox-radius) var(--ox-radius)"},
                        ),
                        className="ox-card-body",
                        style={"padding": ".75rem"},
                    ),
                ],
                className="ox-card",
            ),
            # Error feed
            html.Div(id="dashboard-errors"),
        ],
        className="ox-animate-in",
    )


# ── Callbacks ────────────────────────────────────────────────────────


def register_dashboard_callbacks(app_instance: Dash) -> None:  # noqa: C901
    """Register the periodic dashboard refresh callback."""

    @app_instance.callback(
        Output("kpi-cards-container", "children"),
        Output("dashboard-errors", "children"),
        Output("dashboard-state-store", "data"),
        Output("dashboard-metrics-graph", "extendData"),
        Input("dashboard-interval", "n_intervals"),
        State("dashboard-state-store", "data"),
        prevent_initial_call=False,
    )
    def update_dashboard(n: int, state: dict) -> tuple:
        """Fetch latest metrics and push data to all three chart traces."""
        import dash

        try:
            app = dash.get_app()
            fts = app.flow_tracing_state
            ds = app.data_service
        except Exception as exc:
            placeholder = html.Div(
                f"Initializing\u2026 ({exc})",
                className="ox-empty",
            )
            return placeholder, html.Div(), state, dash.no_update

        # Snapshot current counters and reset for next interval
        active_events = fts.get("active_events", [])
        active_commands = fts.get("active_commands", [])
        errors = fts.get("errors", [])
        event_count = len(active_events)
        command_count = len(active_commands)
        fts["active_events"] = []
        fts["active_commands"] = []

        # Totals from event store
        try:
            stats = ds.get_event_statistics()
            total_events = stats.get("total_events", 0)
            total_aggregates = stats.get("total_aggregates", 0)
        except Exception:
            total_events = event_count
            total_aggregates = 0

        # Rolling history (max 30 points)
        event_history = (state.get("event_history") or []) + [event_count]
        command_history = (state.get("command_history") or []) + [command_count]
        error_history = (state.get("error_history") or []) + [len(errors)]
        event_history = event_history[-30:]
        command_history = command_history[-30:]
        error_history = error_history[-30:]

        new_state = {
            "event_history": event_history,
            "command_history": command_history,
            "error_history": error_history,
        }

        # KPIs + error list
        kpis = kpi_cards(total_events, command_count, len(errors), 0, total_aggregates)
        error_list = dashboard_error_list(errors)

        # Extend all three traces (Events=0, Commands=1, Errors=2)
        now = datetime.datetime.now()
        now_str = now.strftime("%H:%M:%S")

        if n == 0:
            # First render – push the full (possibly single-element) history
            x_vals = [
                (
                    now
                    - datetime.timedelta(
                        seconds=2 * (len(event_history) - i - 1),
                    )
                ).strftime("%H:%M:%S")
                for i in range(len(event_history))
            ]
            extend_data = (
                {
                    "x": [x_vals, x_vals, x_vals],
                    "y": [event_history, command_history, error_history],
                },
                [0, 1, 2],
                60,
            )
        else:
            extend_data = (
                {
                    "x": [[now_str], [now_str], [now_str]],
                    "y": [
                        [event_history[-1]],
                        [command_history[-1]],
                        [error_history[-1]],
                    ],
                },
                [0, 1, 2],
                60,
            )

        return kpis, error_list, new_state, extend_data

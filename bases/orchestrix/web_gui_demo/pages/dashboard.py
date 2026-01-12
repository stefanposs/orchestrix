"""Dashboard page with system overview and KPIs."""

from dash import html, dcc, callback, Output, Input, State

import dash_bootstrap_components as dbc
from components.kpi_cards import kpi_cards
from components.dashboard_chart import dashboard_chart
from components.dashboard_error_list import dashboard_error_list


def dashboard_page():
    """Create the main dashboard page.

    Returns:
        Dashboard layout component
    """
    from components.dashboard_chart import dashboard_chart
    import plotly.graph_objects as go
    # Initialisiere leeres Figure mit 3 Traces (Events, Commands, Errors)
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=[], x=[], mode="lines+markers", name="Events", line={"color": "#1976d2", "width": 2}, marker={"size": 4}, fill="tonexty"))
    fig.add_trace(go.Scatter(y=[], x=[], mode="lines+markers", name="Commands", line={"color": "#00b894", "width": 2}, marker={"size": 4}))
    fig.add_trace(go.Scatter(y=[], x=[], mode="lines+markers", name="Errors", line={"color": "#e17055", "width": 2}, marker={"size": 4}))
    fig.update_layout(
        margin={"t": 40, "b": 20, "l": 20, "r": 20},
        height=300,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
            "bgcolor": "rgba(255,255,255,0.8)",
        },
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font={"size": 12, "family": "Inter, sans-serif"},
        hovermode="x unified",
        xaxis={"showgrid": True, "gridcolor": "#e8eaf6", "range": [0, 30]},
        yaxis={"showgrid": True, "gridcolor": "#e8eaf6", "range": [0, 5]},
    )
    layout = html.Div([
        # Hauptinhalt
        html.Div([
            dcc.Interval(id="dashboard-interval", interval=2*1000, n_intervals=0),
            dcc.Store(id="dashboard-state-store", data={
                "event_history": [],
                "command_history": [],
                "error_history": []
            }),
            html.Div([
                html.H1("System Dashboard", className="dashboard-header"),
                html.P(
                    "Event-sourcing framework for AI-driven, rapid-iteration, enterprise-grade process control.",
                    className="page-subtitle"
                ),
            ], className="mb-4 fade-in"),
            html.Div(id="kpi-cards-container"),
            html.Div([
                html.H4("Live Metrics", className="fw-bold mb-3", style={"color": "var(--primary)"}),
                dcc.Graph(
                    id="dashboard-metrics-graph",
                    figure=fig,
                    config={
                        "displayModeBar": True,
                        "displaylogo": False,
                        "modeBarButtonsToRemove": ["pan2d", "lasso2d"],
                    },
                    animate=True,
                    extendData=None
                )
            ], className="chart-card shadow-hover"),
            html.Div(id="dashboard-errors"),
        ], className="container-fluid", style={"marginLeft": "0px", "transition": "margin-left 0.3s"}),
    ])
    return layout


# Register callback at module level (required by Dash)
def register_dashboard_callbacks(app_instance):
    """Register dashboard callbacks with the app instance."""
    @app_instance.callback(
        Output("kpi-cards-container", "children"),
        Output("dashboard-errors", "children"),
        Output("dashboard-state-store", "data"),
        Output("dashboard-metrics-graph", "extendData"),
        Input("dashboard-interval", "n_intervals"),
        State("dashboard-state-store", "data"),
        State("dashboard-metrics-graph", "figure"),
        prevent_initial_call=False
    )
    def update_dashboard(n: int, state: dict, current_fig) -> tuple:
        """Update dashboard with latest data.

        Args:
            n: Interval counter
            state: Current dashboard state

        Returns:
            Tuple of (kpi_cards, chart, error_list, new_state)
        """
        import dash
        
        try:
            app = dash.get_app()
            flow_tracing_state = app.flow_tracing_state  # type: ignore[attr-defined]
            data_service = app.data_service  # type: ignore[attr-defined]
        except Exception as e:
            # Fallback if app context not available
            return (
                html.Div(f"Initializing... ({str(e)})", className="text-center text-muted py-5"),
                html.Div(),
                html.Div(),
                state
            )
        
        # Get real-time data from flow tracing
        active_events = flow_tracing_state.get("active_events", [])
        active_commands = flow_tracing_state.get("active_commands", [])
        errors = flow_tracing_state.get("errors", [])

        # Zähle aktuelle Events/Commands und leere die Listen für das nächste Intervall
        event_count = len(active_events)
        command_count = len(active_commands)
        flow_tracing_state["active_events"] = []
        flow_tracing_state["active_commands"] = []

        # Die folgenden Variablen werden für die Delta-Berechnung verwendet
        curr_event_count = event_count
        curr_command_count = command_count
        
        # Get statistics from data service (this queries the actual event store)
        try:
            stats = data_service.get_event_statistics()
            total_events = stats.get("total_events", 0)
            total_aggregates = stats.get("total_aggregates", 0)
        except Exception as e:
            # Fallback - use flow tracing data
            total_events = events
            total_aggregates = len(data_service.get_all_aggregate_ids()) if hasattr(data_service, 'get_all_aggregate_ids') else 0
        
        # Update histories in state (keep last 30 data points)
        event_history = state.get("event_history", [])
        command_history = state.get("command_history", [])
        error_history = state.get("error_history", [])
        prev_event_count = state.get("_prev_event_count", 0)
        prev_command_count = state.get("_prev_command_count", 0)


        # Delta ist jetzt einfach die aktuelle Anzahl, weil die Listen immer geleert werden
        event_delta = curr_event_count
        command_delta = curr_command_count

        event_history.append(event_delta)
        command_history.append(command_delta)
        error_history.append(len(errors))

        # Keep only last 30 points
        event_history = event_history[-30:]
        command_history = command_history[-30:]
        error_history = error_history[-30:]

        new_state = {
            "event_history": event_history,
            "command_history": command_history,
            "error_history": error_history,
            "_prev_event_count": curr_event_count,
            "_prev_command_count": curr_command_count
        }

        # Calculate lag (simplified - in real system would compare projection position)
        lag = 0

        # Define 'commands' for KPI cards (number of active commands)
        commands = curr_command_count

        try:
            kpis = kpi_cards(total_events, commands, len(errors), lag, total_aggregates)
            error_list = dashboard_error_list(errors)
        except Exception as e:
            # Fallback on error
            kpis = html.Div(f"Error loading KPIs: {str(e)}", className="text-danger")
            error_list = html.Div(f"Error loading errors: {str(e)}", className="text-danger")

        # extendData: Beim ersten Rendern alle Werte, danach nur den letzten Wert anhängen
        import sys
        print(f"[DASHBOARD DEBUG] n={n}", file=sys.stderr)
        print(f"[DASHBOARD DEBUG] event_history={event_history}", file=sys.stderr)
        print(f"[DASHBOARD DEBUG] command_history={command_history}", file=sys.stderr)
        print(f"[DASHBOARD DEBUG] error_history={error_history}", file=sys.stderr)
        import datetime
        def format_time(ts):
            return ts.strftime("%H:%M:%S")

        if n == 0:
            # Initialdaten: alle bisherigen Werte, mit x-Achse als Uhrzeit
            now = datetime.datetime.now()
            if event_history:
                # Erzeuge Zeitstempel für die letzten n Punkte (jeweils 2 Sekunden auseinander)
                x_vals = [format_time(now - datetime.timedelta(seconds=2*(len(event_history)-i-1))) for i in range(len(event_history))]
                y_vals = event_history
            else:
                x_vals = [format_time(now)]
                y_vals = [0]
            extend_data = (
                {"x": [x_vals], "y": [y_vals]},
                [0],
                500
            )
        else:
            # Nur den letzten Wert anhängen, x ist aktuelle Uhrzeit
            now = datetime.datetime.now()
            x_val = format_time(now)
            if event_history:
                extend_data = (
                    {"x": [[x_val]], "y": [[event_history[-1]]]},
                    [0],
                    500
                )
            else:
                extend_data = (
                    {"x": [[x_val]], "y": [[0]]},
                    [0],
                    500
                )
        print(f"[DASHBOARD DEBUG] extend_data={extend_data}", file=sys.stderr)

        return kpis, error_list, new_state, extend_data

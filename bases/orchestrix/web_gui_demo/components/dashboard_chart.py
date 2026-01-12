"""Dashboard chart component."""

from dash import html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go


def dashboard_chart(event_history: list[int], command_history: list[int], error_history: list[int]) -> html.Div:
    """Create live chart for dashboard metrics.

    Args:
        event_history: List of event counts over time
        command_history: List of command counts over time
        error_history: List of error counts over time

    Returns:
        Chart component
    """
    # Initialisiere leeres Figure mit 3 Traces (Events, Commands, Errors)
    fig = go.Figure()
    fig.add_trace(go.Scatter(y=[], mode="lines+markers", name="Events", line={"color": "#1976d2", "width": 2}, marker={"size": 4}, fill="tonexty"))
    fig.add_trace(go.Scatter(y=[], mode="lines+markers", name="Commands", line={"color": "#00b894", "width": 2}, marker={"size": 4}))
    fig.add_trace(go.Scatter(y=[], mode="lines+markers", name="Errors", line={"color": "#e17055", "width": 2}, marker={"size": 4}))
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
        xaxis={"showgrid": True, "gridcolor": "#e8eaf6"},
        yaxis={"showgrid": True, "gridcolor": "#e8eaf6"},
    )
    return html.Div([
        dbc.Card([
            dbc.CardBody([
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
            ])
        ], className="chart-card shadow-hover")
    ])

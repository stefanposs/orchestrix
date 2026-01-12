"""KPI cards component for dashboard."""

from dash import html
import dash_bootstrap_components as dbc


def kpi_cards(events: int, commands: int, errors: int, lag: int, aggregates: int = 0) -> dbc.Row:
    """Create KPI cards for dashboard.

    Args:
        events: Total number of events
        commands: Number of active commands
        errors: Number of errors
        lag: Projection lag
        aggregates: Total number of aggregates

    Returns:
        Row component with KPI cards
    """
    return dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-lightning-charge-fill kpi-icon", style={"color": "var(--primary)"}),
                        html.H4("Total Events", className="kpi-title mt-2 mb-1"),
                        html.P(f"{events:,}", className="kpi-value mb-0"),
                    ], className="d-flex flex-column align-items-center justify-content-center")
                ])
            ], className="kpi-card shadow-hover"),
            xs=12, sm=6, md=4, lg=2.4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-diagram-3-fill kpi-icon", style={"color": "var(--accent)"}),
                        html.H4("Aggregates", className="kpi-title mt-2 mb-1"),
                        html.P(f"{aggregates:,}", className="kpi-value mb-0"),
                    ], className="d-flex flex-column align-items-center justify-content-center")
                ])
            ], className="kpi-card shadow-hover"),
            xs=12, sm=6, md=4, lg=2.4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-send-fill kpi-icon", style={"color": "var(--success)"}),
                        html.H4("Active Commands", className="kpi-title mt-2 mb-1"),
                        html.P(f"{commands:,}", className="kpi-value mb-0"),
                    ], className="d-flex flex-column align-items-center justify-content-center")
                ])
            ], className="kpi-card shadow-hover"),
            xs=12, sm=6, md=4, lg=2.4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-exclamation-triangle-fill kpi-icon", style={"color": "var(--danger)"}),
                        html.H4("Errors", className="kpi-title mt-2 mb-1"),
                        html.P(f"{errors:,}", className="kpi-value mb-0"),
                    ], className="d-flex flex-column align-items-center justify-content-center")
                ])
            ], className="kpi-card shadow-hover"),
            xs=12, sm=6, md=4, lg=2.4
        ),
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="bi bi-clock-history kpi-icon", style={"color": "var(--warning)"}),
                        html.H4("Projection Lag", className="kpi-title mt-2 mb-1"),
                        html.P(f"{lag}", className="kpi-value mb-0"),
                    ], className="d-flex flex-column align-items-center justify-content-center")
                ])
            ], className="kpi-card shadow-hover"),
            xs=12, sm=6, md=4, lg=2.4
        ),
    ], className="g-4 mb-4")

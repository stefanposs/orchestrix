"""Dashboard error list component."""

from dash import html
import dash_bootstrap_components as dbc


def dashboard_error_list(errors: list[dict]) -> html.Div:
    """Create error list component for dashboard.

    Args:
        errors: List of error dictionaries

    Returns:
        Error list component
    """
    if not errors:
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className="bi bi-check-circle-fill me-2", style={"color": "var(--success)", "fontSize": "1.5rem"}),
                    html.Span("No recent errors", className="text-muted")
                ], className="text-center py-4")
            ])
        ], className="error-card")
    
    # Show last 10 errors
    recent_errors = errors[-10:]
    
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className="bi bi-exclamation-triangle-fill me-2", style={"color": "var(--danger)"}),
                html.H4("Recent Errors", className="fw-bold mb-0 d-inline")
            ], className="mb-3"),
            html.Div([
                html.Div([
                    html.Div([
                        html.Span(
                            error.get("timestamp", "Unknown"),
                            className="badge bg-danger me-2"
                        ),
                        html.Strong(error.get("command", "Unknown command")),
                    ], className="d-flex align-items-center mb-1"),
                    html.Div([
                        html.Small(error.get("error", str(error)), className="text-muted")
                    ]),
                ], className="error-list-item mb-2 p-3")
                for error in reversed(recent_errors)
            ], className="error-list")
        ])
    ], className="error-card shadow-hover")

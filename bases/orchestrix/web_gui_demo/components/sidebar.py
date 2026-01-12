"""Sidebar navigation component."""

from dash import html
import dash_bootstrap_components as dbc


def sidebar() -> html.Div:
    """Create the main sidebar navigation.

    Returns:
        Sidebar component with navigation links
    """
    return html.Div([
        html.Div([
            html.H2("Orchestrix", className="dashboard-header mb-4"),
            html.P("Event-Sourcing Framework", className="text-muted small mb-4"),
        ], className="mb-4"),
        dbc.Nav([
            dbc.NavLink([
                html.I(className="bi bi-speedometer2 me-2"),
                "Dashboard"
            ], href="/", active="exact", className="nav-link"),
            dbc.NavLink([
                html.I(className="bi bi-lightning-charge me-2"),
                "Event Explorer"
            ], href="/events", active="exact", className="nav-link"),
            dbc.NavLink([
                html.I(className="bi bi-diagram-3 me-2"),
                "Aggregate Viewer"
            ], href="/aggregates", active="exact", className="nav-link"),
            dbc.NavLink([
                html.I(className="bi bi-send me-2"),
                "Command Center"
            ], href="/commands", active="exact", className="nav-link"),
        ], vertical=True, pills=True, className="mt-2"),
        html.Div([
            html.Hr(className="my-3"),
            dbc.Button([
                html.I(className="bi bi-question-circle me-2"),
                "Documentation"
            ], href="https://orchestrix-docs.example.com", color="info", className="w-100 mb-2", external_link=True),
            html.Div([
                html.I(className="bi bi-code-slash me-1"),
                "WebGUI v2.0.0"
            ], className="text-muted text-center small mt-2")
        ], className="sidebar-footer")
    ], className="sidebar")

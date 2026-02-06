"""Orchestrix Web GUI - Enterprise-ready Dash application."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State

from .components.sidebar import sidebar
from .demo_bootstrap import bootstrap_demo
from .pages import PAGES
from .services.data_service import DataService
from .services.process_service import ProcessService

# Initialize Dash app with modern theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css",
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
        "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&display=swap",
    ],
    suppress_callback_exceptions=True,
)

# Backend objects
event_store, _aggregate_store, message_bus, flow_tracing_state, trace_command, trace_event = (
    bootstrap_demo()
)

# Services
data_service = DataService(event_store, message_bus)
process_service = ProcessService()

# ---- Layout ----
app.layout = html.Div(
    [
        dcc.Location(id="url"),
        dcc.Store(id="sidebar-visible-store", data=True),
        # Shell: sidebar + main
        html.Div(
            [
                sidebar(),
                html.Div(
                    [
                        # Topbar
                        html.Div(
                            [
                                html.Button(
                                    html.I(className="bi bi-list"),
                                    id="sidebar-hamburger-btn",
                                    n_clicks=0,
                                    className="ox-topbar-toggle",
                                ),
                                html.Span(id="topbar-page-title", className="ox-topbar-title"),
                                html.Div(className="ox-topbar-spacer"),
                                html.Div(
                                    [
                                        html.Span(className="ox-topbar-status-dot"),
                                        "Live",
                                    ],
                                    className="ox-topbar-status",
                                ),
                            ],
                            className="ox-topbar",
                        ),
                        # Page content
                        html.Div(
                            html.Div(id="page-content", className="ox-page"),
                        ),
                    ],
                    id="main-area",
                    className="ox-main",
                ),
            ],
            className="ox-shell",
        ),
    ]
)


# ---- Callbacks ----
@app.callback(
    Output("main-sidebar", "className"),
    Output("main-area", "className"),
    Output("sidebar-visible-store", "data"),
    Input("sidebar-hamburger-btn", "n_clicks"),
    State("sidebar-visible-store", "data"),
    prevent_initial_call=True,
)
def toggle_sidebar(n_clicks: int, visible: bool):
    """Toggle sidebar visibility and update CSS classes."""
    new_visible = not visible
    sidebar_cls = "ox-sidebar" if new_visible else "ox-sidebar collapsed"
    main_cls = "ox-main" if new_visible else "ox-main expanded"
    return sidebar_cls, main_cls, new_visible


PAGE_TITLES = {
    "/": "Dashboard",
    "/events": "Event Explorer",
    "/aggregates": "Aggregate Viewer",
    "/commands": "Command Center",
    "/processes": "Processes",
}


@app.callback(
    Output("page-content", "children"),
    Output("topbar-page-title", "children"),
    Input("url", "pathname"),
)
def render_page_content(pathname: str):
    """Render the page layout for the current URL."""
    title = PAGE_TITLES.get(pathname, "Orchestrix")

    page = PAGES.get(pathname)
    if page:
        return page(), title

    # Dynamic aggregate details route
    aggregate_details_router = PAGES.get("/aggregates/<id>")
    if aggregate_details_router and pathname.startswith("/aggregates/"):
        details_view = aggregate_details_router(pathname)
        if details_view:
            return details_view, "Aggregate Details"

    return html.H2("404: Page not found", className="text-danger"), "Not Found"


# Make services available to pages via app context
app.data_service = data_service  # type: ignore[attr-defined]
app.flow_tracing_state = flow_tracing_state  # type: ignore[attr-defined]
app.process_service = process_service  # type: ignore[attr-defined]

# Register all callbacks
from .pages import register_dashboard_callbacks  # noqa: E402

register_dashboard_callbacks(app)

from .pages import (  # noqa: E402, F401
    aggregate_viewer,
    command_center,
    event_explorer,
)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)

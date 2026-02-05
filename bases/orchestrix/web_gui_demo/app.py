"""Orchestrix Web GUI - Enterprise-ready Dash application."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output

from components.sidebar import sidebar
from demo_bootstrap import bootstrap_demo
from pages import PAGES
from services.data_service import DataService

# Initialize Dash app with modern theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css",
        "/assets/dashboard_theme.css",
        "/assets/notion_table.css",
    ],
    suppress_callback_exceptions=True,
)

# Backend-Objekte
event_store, aggregate_store, message_bus, flow_tracing_state, trace_command, trace_event = (
    bootstrap_demo()
)

# Initialize data service
data_service = DataService(event_store, message_bus)

# Initialize process service
from services.process_service import ProcessService  # noqa: E402

process_service = ProcessService()

content = html.Div(id="page-content", className="p-4")

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Store(id="sidebar-visible-store", data=True),
    # Topbar mit Hamburger-Icon
    html.Div([
        html.Button(
            html.I(className="bi bi-list", style={"fontSize": "1.5rem"}),
            id="sidebar-hamburger-btn",
            n_clicks=0,
            className="btn btn-link p-0 ms-2",
            style={"background": "none", "border": "none", "outline": "none", "marginTop": "8px"}
        ),
        html.Span("Orchestrix", className="navbar-brand ms-2 fw-bold", style={"fontSize": "1.3rem"}),
    ], style={"height": "48px", "display": "flex", "alignItems": "center", "background": "#f8f9fa", "borderBottom": "1px solid #e0e0e0", "zIndex": 1001, "position": "relative"}),
    dbc.Container([
        dbc.Row([
            dbc.Col(sidebar(), width=2, className="sidebar-col", id="sidebar-col"),
            dbc.Col(content, width=10, className="main-content bg-white p-4 rounded-4 shadow-sm"),
        ], className="g-0", style={"height": "calc(100vh - 48px)"})
    ], fluid=True)
])

# Callback: Sidebar ein-/ausblenden
@app.callback(
    Output("sidebar-col", "style"),
    Output("sidebar-visible-store", "data"),
    Input("sidebar-hamburger-btn", "n_clicks"),
    State("sidebar-visible-store", "data"),
    prevent_initial_call=False
)
def toggle_sidebar(n_clicks, visible):
    if n_clicks is None:
        raise dash.exceptions.PreventUpdate
    # Toggle Sichtbarkeit
    new_visible = not visible if n_clicks else True
    style = {"display": "block"} if new_visible else {"display": "none"}
    return style, new_visible

@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname: str):
    """Render the page layout for the current URL."""
    page = PAGES.get(pathname)
    if page:
        return page()
    # Check for dynamic process details route
    process_details_router = PAGES.get("/processes/<id>")
    if process_details_router:
        details_view = process_details_router(pathname)
        if details_view:
            return details_view
    # Check for dynamic aggregate details route
    aggregate_details_router = PAGES.get("/aggregates/<id>")
    if aggregate_details_router:
        details_view = aggregate_details_router(pathname)
        if details_view:
            return details_view
    return html.H2("404: Page not found", className="text-danger")

# Make services available to pages via app context
app.data_service = data_service  # type: ignore[attr-defined]
app.flow_tracing_state = flow_tracing_state  # type: ignore[attr-defined]
app.process_service = process_service  # type: ignore[attr-defined]

# Register dashboard callbacks
from pages import register_dashboard_callbacks  # noqa: E402

register_dashboard_callbacks(app)

# Import other pages to ensure their modules are loaded and callbacks registered
from pages import (  # noqa: E402, F401
    event_explorer,
    aggregate_viewer,
    command_center,
)

if __name__ == "__main__":
    # dash>=3 deprecates run_server in favor of run
    app.run(debug=True, host="0.0.0.0", port=8050)

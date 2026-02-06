import dash_bootstrap_components as dbc
from dash import dcc, html


def settings_page() -> html.Div:
    """Render the settings page with theme, API and RBAC controls."""
    return html.Div(
        [
            html.H1("Settings"),
            dbc.Form(
                [
                    dbc.Label("Theme"),
                    dcc.Dropdown(
                        options=[
                            {"label": "Light", "value": "light"},
                            {"label": "Dark", "value": "dark"},
                        ],
                        value="light",
                        id="theme-dropdown",
                        clearable=False,
                        className="mb-3",
                    ),
                    dbc.Label("API Endpoint"),
                    dbc.Input(
                        type="text",
                        placeholder="https://api.orchestrix.local",
                        className="mb-3",
                        id="api-endpoint-input",
                    ),
                    dbc.Label("RBAC Role"),
                    dcc.Dropdown(
                        options=[
                            {"label": "Admin", "value": "admin"},
                            {"label": "User", "value": "user"},
                        ],
                        value="user",
                        id="rbac-dropdown",
                        clearable=False,
                        className="mb-3",
                    ),
                    dbc.Button("Save Settings", color="primary", id="save-settings-btn"),
                ],
                className="p-4 bg-white rounded shadow border mb-4",
            ),
            html.Hr(),
            html.P(
                "Orchestrix Core Version: 1.0.0 | Schema Version: 1.0.0 | GUI Version: 1.0.0",
                className="text-secondary",
            ),
        ],
        className="p-4",
    )

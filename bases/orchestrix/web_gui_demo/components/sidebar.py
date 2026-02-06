"""Sidebar navigation component."""

import dash_bootstrap_components as dbc
from dash import html


def _nav_item(icon: str, label: str, href: str) -> dbc.NavLink:
    """Create a sidebar navigation item."""
    return dbc.NavLink(
        [html.I(className=f"bi bi-{icon}"), label],
        href=href,
        active="exact",
    )


def sidebar() -> html.Div:
    """Create the main sidebar navigation.

    Returns:
        Sidebar component with navigation links

    """
    return html.Div(
        [
            # Brand
            html.Div(
                [
                    html.Div(
                        html.I(className="bi bi-boxes"),
                        className="ox-sidebar-brand-icon",
                    ),
                    html.Div(
                        [
                            html.Span("Orchestrix", className="ox-sidebar-brand-text"),
                            html.Span(
                                "Event-Sourcing Framework",
                                className="ox-sidebar-brand-sub",
                            ),
                        ]
                    ),
                ],
                className="ox-sidebar-brand",
            ),
            # Section: Overview
            html.Div("Overview", className="ox-sidebar-section"),
            dbc.Nav(
                [
                    _nav_item("grid-1x2-fill", "Dashboard", "/"),
                    _nav_item("lightning-charge-fill", "Event Explorer", "/events"),
                    _nav_item("diagram-3-fill", "Aggregate Viewer", "/aggregates"),
                ],
                vertical=True,
                pills=True,
            ),
            # Section: Actions
            html.Div("Actions", className="ox-sidebar-section"),
            dbc.Nav(
                [
                    _nav_item("send-fill", "Command Center", "/commands"),
                    _nav_item("arrow-repeat", "Processes", "/processes"),
                ],
                vertical=True,
                pills=True,
            ),
            # Footer
            html.Div(
                [
                    html.Div(
                        [html.I(className="bi bi-code-slash me-1"), " v2.2.0"],
                    ),
                ],
                className="ox-sidebar-footer",
            ),
        ],
        id="main-sidebar",
        className="ox-sidebar",
    )

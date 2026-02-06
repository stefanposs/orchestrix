"""Processes page – browse and manage predefined processes."""

from dash import html


def processes_page() -> html.Div:
    """Render the processes overview page."""
    return html.Div(
        [
            # Header
            html.Div(
                [
                    html.H1("Processes", className="ox-page-title"),
                    html.P(
                        "Predefined process workflows are managed via the Command Center",
                        className="ox-page-subtitle",
                    ),
                ],
                className="ox-page-header",
            ),
            # Info card
            html.Div(
                [
                    html.Div(
                        html.H3(
                            [html.I(className="bi bi-arrow-repeat me-2"), "Process Overview"],
                            className="ox-card-title",
                        ),
                        className="ox-card-header",
                    ),
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.I(
                                        className="bi bi-info-circle",
                                        style={
                                            "fontSize": "2.5rem",
                                            "color": "var(--ox-primary)",
                                            "opacity": ".5",
                                        },
                                    ),
                                    html.P(
                                        "Process execution and management has moved "
                                        "to the Command Center.",
                                        style={"margin": ".75rem 0 .25rem"},
                                    ),
                                    html.Small(
                                        "Navigate to Command Center to view, search "
                                        "and execute predefined processes.",
                                        style={"opacity": ".6"},
                                    ),
                                    html.A(
                                        [
                                            html.I(className="bi bi-send me-1"),
                                            "Go to Command Center",
                                        ],
                                        href="/commands",
                                        className="ox-btn ox-btn-primary",
                                        style={
                                            "display": "inline-flex",
                                            "marginTop": "1.25rem",
                                            "textDecoration": "none",
                                        },
                                    ),
                                ],
                                className="ox-empty",
                            ),
                        ],
                        className="ox-card-body",
                    ),
                ],
                className="ox-card",
            ),
        ],
        className="ox-animate-in",
    )


def process_details_page(process_id: str) -> html.Div:
    """Render the details page for a single process.

    Args:
        process_id: The ID of the process to show.

    Returns:
        Dash layout for the process details view.

    """
    return html.Div(
        [
            html.A(
                [html.I(className="bi bi-arrow-left me-1"), "Back to Processes"],
                href="/processes",
                className="ox-btn ox-btn-secondary",
                style={
                    "display": "inline-flex",
                    "marginBottom": "1rem",
                    "textDecoration": "none",
                },
            ),
            html.Div(
                [
                    html.Div(
                        html.H3(
                            f"Process: {process_id}",
                            className="ox-card-title",
                        ),
                        className="ox-card-header",
                    ),
                    html.Div(
                        [
                            html.P(
                                "Process details are managed via the Command Center.",
                                style={"opacity": ".7"},
                            ),
                            html.A(
                                "View in Command Center",
                                href="/commands",
                                className="ox-btn ox-btn-primary",
                                style={"textDecoration": "none"},
                            ),
                        ],
                        className="ox-card-body",
                    ),
                ],
                className="ox-card",
            ),
        ],
        className="ox-animate-in",
    )

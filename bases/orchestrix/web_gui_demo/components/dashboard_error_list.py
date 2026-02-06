"""Dashboard error list component."""

from datetime import datetime

from dash import html


def _format_timestamp(ts: object) -> str:
    """Format a timestamp value to human-readable string."""
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(ts).strftime("%H:%M:%S")  # noqa: DTZ006
        except (OSError, ValueError):
            return str(ts)
    return str(ts) if ts else "?"


def dashboard_error_list(errors: list[dict]) -> html.Div:
    """Render recent errors or a success placeholder."""
    if not errors:
        return html.Div(
            [
                html.Div(
                    [
                        html.I(
                            className="bi bi-check-circle-fill",
                            style={
                                "color": "var(--ox-success)",
                                "fontSize": "2rem",
                            },
                        ),
                        html.P(
                            "No recent errors",
                            style={"margin": ".5rem 0 0", "opacity": ".6"},
                        ),
                        html.Small(
                            "All systems operating normally",
                            style={"opacity": ".4"},
                        ),
                    ],
                    className="ox-empty",
                ),
            ],
            className="ox-card",
        )

    recent = errors[-10:]

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.I(
                                className="bi bi-exclamation-triangle-fill",
                                style={"color": "var(--ox-danger)"},
                            ),
                            html.H3(
                                " Recent Errors",
                                className="ox-card-title",
                                style={"display": "inline"},
                            ),
                        ],
                        style={"display": "flex", "alignItems": "center", "gap": ".5rem"},
                    ),
                    html.Span(
                        str(len(recent)),
                        className="ox-badge ox-badge-danger",
                    ),
                ],
                className="ox-card-header",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                _format_timestamp(err.get("timestamp")),
                                className="ox-badge ox-badge-danger",
                                style={"marginRight": ".65rem"},
                            ),
                            html.Strong(
                                str(err.get("command", "Unknown"))[:60],
                                style={"fontSize": ".85rem"},
                            ),
                            html.Br(),
                            html.Small(
                                str(err.get("error", str(err)))[:120],
                                style={"opacity": ".55", "fontSize": ".8rem"},
                            ),
                        ],
                        className="ox-error-item",
                    )
                    for err in reversed(recent)
                ],
                className="ox-card-body",
                style={"padding": ".75rem 1rem"},
            ),
        ],
        className="ox-card",
        style={"marginTop": "1.5rem"},
    )

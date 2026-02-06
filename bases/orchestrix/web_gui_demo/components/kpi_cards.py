"""KPI cards component for dashboard."""

from dash import html


def _kpi(icon_cls: str, color_cls: str, label: str, value: str) -> html.Div:
    """Create a single KPI card."""
    return html.Div(
        [
            html.Div(
                html.I(className=f"bi bi-{icon_cls}"),
                className=f"ox-kpi-icon {color_cls}",
            ),
            html.Div(
                [
                    html.Div(label, className="ox-kpi-label"),
                    html.Div(value, className="ox-kpi-value"),
                ],
                className="ox-kpi-body",
            ),
        ],
        className="ox-kpi",
    )


def kpi_cards(
    events: int,
    commands: int,
    errors: int,
    lag: int,
    aggregates: int = 0,
) -> html.Div:
    """Create KPI cards row for dashboard.

    Args:
        events: Total number of events
        commands: Number of active commands
        errors: Number of errors
        lag: Projection lag
        aggregates: Total number of aggregates

    Returns:
        Grid of KPI cards

    """
    return html.Div(
        [
            _kpi("lightning-charge-fill", "events", "Total Events", f"{events:,}"),
            _kpi("diagram-3-fill", "aggs", "Aggregates", f"{aggregates:,}"),
            _kpi("send-fill", "commands", "Active Commands", f"{commands:,}"),
            _kpi("exclamation-triangle-fill", "errors", "Errors", f"{errors:,}"),
            _kpi("clock-history", "lag", "Projection Lag", str(lag)),
        ],
        className="ox-kpi-row",
    )

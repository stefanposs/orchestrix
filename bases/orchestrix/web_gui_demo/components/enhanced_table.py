"""Enhanced table components with filtering and search."""

from typing import Any

import dash_bootstrap_components as dbc
from dash import dash_table, html


def create_enhanced_table(
    data: list[dict[str, Any]],
    columns: list[dict[str, Any]],
    table_id: str,
    search_placeholder: str = "Search...",
    page_size: int = 10,
) -> html.Div:
    """Create an enhanced table with search and filtering.

    Args:
        data: List of dictionaries representing table rows
        columns: List of column definitions for dash_table
        table_id: Unique ID for the table
        search_placeholder: Placeholder text for search input
        page_size: Number of rows per page

    Returns:
        Enhanced table component with search and filters

    """
    return html.Div(
        [
            dbc.InputGroup(
                [
                    dbc.InputGroupText([html.I(className="bi bi-search")]),
                    dbc.Input(
                        id=f"{table_id}-search",
                        placeholder=search_placeholder,
                        type="text",
                        className="mb-3",
                    ),
                ],
                className="mb-3",
            ),
            dash_table.DataTable(
                id=table_id,
                columns=columns,
                data=data,  # type: ignore[arg-type]
                page_size=page_size,
                page_action="native",
                sort_action="native",
                filter_action="native",
                style_table={
                    "overflowX": "auto",
                    "borderRadius": "0.5rem",
                },
                style_header={
                    "backgroundColor": "#1976d2",
                    "color": "white",
                    "fontWeight": "bold",
                    "textAlign": "left",
                    "padding": "12px",
                },
                style_cell={
                    "textAlign": "left",
                    "padding": "10px",
                    "fontFamily": "Inter, sans-serif",
                    "fontSize": "0.875rem",
                },
                style_data={
                    "whiteSpace": "normal",
                    "height": "auto",
                },
                style_data_conditional=[
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "#f8f9fa",
                    },
                    {
                        "if": {"state": "selected"},
                        "backgroundColor": "#e3f2fd",
                        "border": "1px solid #1976d2",
                    },
                ],
                css=[
                    {
                        "selector": ".dash-table-tooltip",
                        "rule": "font-family: Inter, sans-serif",
                    },
                ],
            ),
        ],
        className="enhanced-table-container",
    )


def create_simple_table(
    data: list[dict[str, Any]],
    columns: list[str],
    table_id: str | None = None,
) -> dbc.Table:
    """Create a simple Bootstrap table.

    Args:
        data: List of dictionaries with column keys
        columns: List of column names
        table_id: Optional table ID

    Returns:
        Bootstrap table component

    """
    if not data:
        return dbc.Table(
            [
                html.Thead(html.Tr([html.Th(col) for col in columns])),
                html.Tbody(
                    [
                        html.Tr(
                            [
                                html.Td(
                                    "No data available",
                                    colSpan=len(columns),
                                    className="text-center text-muted py-4",
                                )
                            ]
                        )
                    ]
                ),
            ],
            bordered=True,
            hover=True,
            responsive=True,
            striped=True,
            className="table-card",
            id=table_id,
        )

    table_header = html.Thead(html.Tr([html.Th(col, className="fw-bold") for col in columns]))

    table_rows = []
    for row in data:
        table_rows.append(html.Tr([html.Td(row.get(col, "-")) for col in columns]))

    table_body = html.Tbody(table_rows)

    return dbc.Table(
        [table_header, table_body],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        className="table-card",
        id=table_id,
    )

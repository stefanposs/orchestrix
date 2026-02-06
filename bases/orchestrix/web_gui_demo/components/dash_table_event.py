import dash_bootstrap_components as dbc
import dash_table
import pandas as pd
from dash import html


def dash_event_table(
    events: list[dict[str, str]],
    table_id: str = "event-table",
) -> html.Div:
    """Build a Dash DataTable with filter, pagination, and CSV download."""
    if not events:
        df = pd.DataFrame(columns=pd.Index(["ID", "Type", "Payload"]))
    else:
        df = pd.DataFrame(
            [
                {
                    "ID": evt.get("id", ""),
                    "Type": evt.get("type", ""),
                    "Payload": str(evt.get("payload", "")),
                }
                for evt in events
            ]
        )

    table = dash_table.DataTable(
        id=table_id,
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict("records"),
        page_size=10,
        filter_action="native",
        sort_action="native",
        style_table={
            "overflowX": "auto",
            "borderRadius": "12px",
            "boxShadow": "0 2px 8px rgba(60,60,60,0.04)",
            "borderCollapse": "separate",
            "borderSpacing": "0",
            "background": "#fff",
        },
        style_cell={
            "textAlign": "left",
            "fontFamily": "Inter, 'Segoe UI', Arial, sans-serif",
            "fontSize": "1rem",
            "color": "#444",
            "padding": "0.75rem 1rem",
        },
        style_header={"fontWeight": "600", "backgroundColor": "#f6f7f9", "color": "#3a3a3a"},
        style_data={"backgroundColor": "#fff"},
        style_data_conditional=[{"if": {"row_index": "even"}, "backgroundColor": "#fafbfc"}],
        export_format="csv",
        export_headers="display",
    )
    download_btn = dbc.Button(
        "Download CSV",
        id=f"{table_id}-download-btn",
        color="secondary",
        className="mb-2",
        n_clicks=0,
    )
    return html.Div([download_btn, table], className="mb-4")


# Example callback for CSV download (if custom logic needed)
# @app.callback(
#     Output("download-data", "data"),
#     Input("event-table-download-btn", "n_clicks"),
#     State("event-table", "data"),
#     prevent_initial_call=True
# )
# def download_csv(n_clicks, table_data):
#     if n_clicks and table_data:
#         df = pd.DataFrame(table_data)
#         csv_string = df.to_csv(index=False)
#         b64 = base64.b64encode(csv_string.encode()).decode()
#         return dict(content=b64, filename="events.csv", base64=True)
#     return None

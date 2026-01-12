# processes.py
# Implements the Process page with tiles for custom processes, each with a form for command or CSV upload.

from dash import html, dcc

import dash_bootstrap_components as dbc
import dash_bootstrap_components as dbc

# Dummy process list for demonstration
PROCESSES = [
    {"id": "PROC-001", "name": "Prozess A", "description": "CSV-Upload und Command"},
    {"id": "PROC-002", "name": "Prozess B", "description": "Nur Command"},
]

def processes_page():
    """Renders the process page as a table of processes with details button."""
    table_header = html.Thead(html.Tr([
        html.Th("Prozess ID"),
        html.Th("Name"),
        html.Th("Beschreibung"),
        html.Th("Aktion")
    ]))
    table_body = html.Tbody([
        html.Tr([
            html.Td(proc["id"]),
            html.Td(proc["name"]),
            html.Td(proc["description"]),
            html.Td(
                dbc.Button("Details", href=f"/processes/{proc['id']}", color="primary", size="sm")
            )
        ]) for proc in PROCESSES
    ])
    return html.Div([
        html.H2("Prozess Explorer"),
        dbc.Table([
            table_header,
            table_body
        ], bordered=True, hover=True, responsive=True, striped=True, className="bg-white shadow rounded"),
    ], className="p-4")

# Details page for a single process
def process_details_page(process_id: str):
    """Renders the details page for a single process.

    Parameters:
        process_id (str): The ID of the process to show.

    Returns:
        Dash layout for the process details view.
    """
    proc = next((p for p in PROCESSES if p["id"] == process_id), None)
    if not proc:
        return html.Div([html.H3("Prozess nicht gefunden", className="text-danger")], className="p-4")
    checklist = dbc.Checklist(
        options=[
            {"label": "Schritt 1: Vorbereitung", "value": 1},
            {"label": "Schritt 2: Daten prüfen", "value": 2},
            {"label": "Schritt 3: Command ausführen", "value": 3},
        ],
        value=[],
        id="process-checklist",
        inline=False,
        className="mb-3"
    )
    upload = dcc.Upload(
        id="process-upload",
        children=html.Button("CSV/JSON hochladen"),
        style={"marginBottom": "10px"}
    )
    command_input = dcc.Input(
        id="process-command-input",
        type="text",
        placeholder="Command Parameter",
        style={"marginBottom": "10px"}
    )
    run_btn = html.Button("Command ausführen", id="process-run-btn", className="btn btn-success")
    return html.Div([
        html.H2(f"Prozess: {proc['name']} ({proc['id']})"),
        html.P(proc["description"]),
        html.H5("Checkliste"),
        checklist,
        html.Hr(),
        html.H5("Command ausführen"),
        upload,
        command_input,
        run_btn
    ], className="p-4 bg-light rounded shadow")

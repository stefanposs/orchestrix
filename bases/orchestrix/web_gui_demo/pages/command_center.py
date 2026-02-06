"""Command Center – dispatch commands and run predefined processes."""

import json
from typing import TypedDict

import dash_table
from dash import Input, Output, State, callback, dcc, html
from dash.dependencies import ALL

# ── Sample command schemas ───────────────────────────────────────────


class _FieldDef(TypedDict):
    """Schema for a command field definition."""

    name: str
    label: str
    type: str
    required: bool


class _CommandDef(TypedDict):
    """Schema for a sample command definition."""

    name: str
    description: str
    fields: list[_FieldDef]


SAMPLE_COMMANDS: list[_CommandDef] = [
    {
        "name": "CreateOrder",
        "description": "Create a new order",
        "fields": [
            {"name": "order_id", "label": "Order ID", "type": "text", "required": True},
            {"name": "customer_name", "label": "Customer Name", "type": "text", "required": True},
            {"name": "total_amount", "label": "Total Amount", "type": "number", "required": True},
        ],
    },
    {
        "name": "CancelOrder",
        "description": "Cancel an existing order",
        "fields": [
            {"name": "order_id", "label": "Order ID", "type": "text", "required": True},
        ],
    },
]


# ── Page layout ──────────────────────────────────────────────────────


def command_center_page() -> html.Div:
    """Create the command center page layout."""
    command_options = [
        {"label": f"{c['name']} \u2013 {c.get('description', '')}", "value": c["name"]}
        for c in SAMPLE_COMMANDS
    ]

    return html.Div(
        [
            # Header
            html.Div(
                [
                    html.H1("Command Center", className="ox-page-title"),
                    html.P(
                        "Dispatch commands to the event-sourcing system",
                        className="ox-page-subtitle",
                    ),
                ],
                className="ox-page-header",
            ),
            # ── Processes section ────────────────────────────────────
            html.Div(
                [
                    html.Div(
                        [
                            html.H3(
                                [html.I(className="bi bi-list-task"), " Predefined Processes"],
                                className="ox-card-title",
                            ),
                            dcc.Input(
                                id="process-search-input",
                                placeholder="Search processes\u2026",
                                type="text",
                                className="ox-input",
                                style={"width": "100%", "marginTop": ".75rem"},
                            ),
                        ],
                        className="ox-card-header",
                    ),
                    html.Div(id="process-table-container", className="ox-card-body"),
                    html.Div(id="process-execution-feedback"),
                ],
                className="ox-card",
            ),
            # ── Command dispatch row ─────────────────────────────────
            html.Div(
                [
                    # Left: form + batch JSON
                    html.Div(
                        [
                            # Single command
                            html.Div(
                                [
                                    html.Div(
                                        html.H3(
                                            [html.I(className="bi bi-send"), " Dispatch Command"],
                                            className="ox-card-title",
                                        ),
                                        className="ox-card-header",
                                    ),
                                    html.Div(
                                        [
                                            html.Label("Command Type", className="ox-label"),
                                            dcc.Dropdown(
                                                options=command_options,
                                                value=str(SAMPLE_COMMANDS[0]["name"]),
                                                id="command-type-dropdown",
                                                clearable=False,
                                                className="ox-dropdown",
                                            ),
                                            html.Div(
                                                id="command-form-fields",
                                                style={"marginTop": "1rem"},
                                            ),
                                            html.Button(
                                                [
                                                    html.I(className="bi bi-send-fill me-1"),
                                                    "Send Command",
                                                ],
                                                id="send-command-btn",
                                                n_clicks=0,
                                                className="ox-btn ox-btn-primary",
                                                style={"width": "100%", "marginTop": "1rem"},
                                            ),
                                            html.Div(
                                                id="command-feedback",
                                                style={"marginTop": ".75rem"},
                                            ),
                                        ],
                                        className="ox-card-body",
                                    ),
                                ],
                                className="ox-card",
                            ),
                            # Batch JSON
                            html.Div(
                                [
                                    html.Div(
                                        html.H3(
                                            [
                                                html.I(className="bi bi-code-slash"),
                                                " Batch Commands (JSON)",
                                            ],
                                            className="ox-card-title",
                                        ),
                                        className="ox-card-header",
                                    ),
                                    html.Div(
                                        [
                                            html.Label(
                                                "JSON Array of Commands",
                                                className="ox-label",
                                            ),
                                            dcc.Textarea(
                                                id="command-json-array",
                                                placeholder=(
                                                    '[{"order_id": "123", '
                                                    '"customer_name": "Alice", '
                                                    '"total_amount": 99.99}]'
                                                ),
                                                className="ox-input",
                                                style={
                                                    "width": "100%",
                                                    "minHeight": "120px",
                                                    "fontFamily": "var(--ox-font-mono)",
                                                },
                                            ),
                                            html.Button(
                                                [
                                                    html.I(className="bi bi-send-fill me-1"),
                                                    "Send JSON Array",
                                                ],
                                                id="send-json-array-btn",
                                                n_clicks=0,
                                                className="ox-btn ox-btn-success",
                                                style={
                                                    "width": "100%",
                                                    "marginTop": ".75rem",
                                                },
                                            ),
                                            html.Div(
                                                id="json-array-feedback",
                                                style={"marginTop": ".75rem"},
                                            ),
                                        ],
                                        className="ox-card-body",
                                    ),
                                ],
                                className="ox-card",
                                style={"marginTop": "1.5rem"},
                            ),
                        ],
                        style={"flex": "1 1 0%", "minWidth": 0},
                    ),
                    # Right: schema info
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Div(
                                        html.H3(
                                            [
                                                html.I(className="bi bi-info-circle"),
                                                " Command Schemas",
                                            ],
                                            className="ox-card-title",
                                        ),
                                        className="ox-card-header",
                                    ),
                                    html.Div(id="command-schema-info", className="ox-card-body"),
                                ],
                                className="ox-card",
                            ),
                        ],
                        style={"flex": "1 1 0%", "minWidth": 0},
                    ),
                ],
                style={"display": "flex", "gap": "1.5rem", "marginTop": "1.5rem"},
            ),
        ],
        className="ox-animate-in",
    )


# ── Callbacks ────────────────────────────────────────────────────────


@callback(
    Output("process-table-container", "children"),
    Input("process-table-container", "id"),
    Input("process-search-input", "value"),
    prevent_initial_call=False,
)
def render_process_table(_: str, search_text: str | None) -> html.Div:
    """Render predefined processes table with execute buttons."""
    import dash

    try:
        ps = dash.get_app().process_service
        processes = ps.get_all_processes()
    except Exception:
        processes = []

    if search_text:
        q = search_text.lower()
        processes = [
            p
            for p in processes
            if q in str(p.get("id", "")).lower()
            or q in str(p.get("name", "")).lower()
            or q in str(p.get("description", "")).lower()
        ]

    if not processes:
        return html.Div(
            [
                html.I(className="bi bi-inbox", style={"fontSize": "2rem", "opacity": ".4"}),
                html.P("No processes found"),
            ],
            className="ox-empty",
        )

    table_data = [
        {
            "Name": p.get("name", "N/A"),
            "Description": p.get("description", "N/A"),
            "Category": p.get("category", "N/A"),
            "Commands": len(p.get("command_sequence", [])),
        }
        for p in processes
    ]

    table = dash_table.DataTable(
        id="process-data-table",
        columns=[
            {"name": "Name", "id": "Name"},
            {"name": "Description", "id": "Description"},
            {"name": "Category", "id": "Category"},
            {"name": "Commands", "id": "Commands", "type": "numeric"},
        ],
        data=table_data,
        page_size=10,
        sort_action="native",
        style_table={"overflowX": "auto", "borderRadius": "var(--ox-radius)"},
        style_header={
            "backgroundColor": "var(--ox-bg-subtle)",
            "color": "var(--ox-text-secondary)",
            "fontWeight": "600",
            "textAlign": "left",
            "padding": "10px 14px",
            "border": "none",
            "fontSize": ".78rem",
            "textTransform": "uppercase",
            "letterSpacing": ".04em",
            "borderBottom": "2px solid var(--ox-border)",
        },
        style_cell={
            "textAlign": "left",
            "padding": "10px 14px",
            "fontFamily": "Inter, sans-serif",
            "fontSize": ".85rem",
            "border": "none",
            "borderBottom": "1px solid var(--ox-border-light)",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "var(--ox-bg-subtle)",
            },
        ],
    )

    buttons = html.Div(
        [
            html.Button(
                [html.I(className="bi bi-play-fill"), f" Execute {p.get('id')}"],
                id={"type": "execute-process-btn", "index": p.get("id")},
                className="ox-btn ox-btn-secondary",
                style={"marginRight": ".5rem", "marginBottom": ".5rem", "fontSize": ".8rem"},
            )
            for p in processes
        ],
        style={"marginTop": ".75rem"},
    )

    return html.Div(
        [
            table,
            html.Hr(),
            html.H4("Quick Actions", className="ox-card-title"),
            buttons,
        ]
    )


@callback(
    Output("process-execution-feedback", "children", allow_duplicate=True),
    Input({"type": "execute-process-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def execute_process(n_clicks_list: list[int | None]) -> html.Div:
    """Execute a predefined process."""
    import dash

    ctx = dash.callback_context
    if not ctx.triggered:
        return html.Div()

    button_id = ctx.triggered[0]["prop_id"]
    if "execute-process-btn" not in button_id:
        return html.Div()

    try:
        button_data = json.loads(button_id.split(".")[0])
        process_id = button_data["index"]
    except Exception:
        return html.Div()

    try:
        app = dash.get_app()
        result = app.process_service.execute_process(process_id, app.data_service)
        status = result.get("status", "error")
        msg = result.get("message", "Unknown")

        if status == "success":
            cls = "ox-alert ox-alert-success"
        elif status == "partial":
            cls = "ox-alert ox-alert-warning"
        else:
            cls = "ox-alert ox-alert-danger"

        return html.Div(msg, className=cls)
    except Exception as exc:
        return html.Div(f"Error: {exc}", className="ox-alert ox-alert-danger")


@callback(
    Output("command-form-fields", "children"),
    Output("command-schema-info", "children"),
    Input("command-type-dropdown", "value"),
)
def update_form_fields(command_type: str) -> tuple:
    """Generate form fields and schema info for the selected command."""
    cmd = next((c for c in SAMPLE_COMMANDS if c["name"] == command_type), SAMPLE_COMMANDS[0])

    form_fields = []
    for f in cmd["fields"]:
        req = " *" if f.get("required") else ""
        form_fields.append(
            dcc.Input(
                id=f"cmd_{f['name']}",
                placeholder=f["label"] + req,
                type=f["type"],  # type: ignore[arg-type]
                className="ox-input",
                style={"width": "100%", "marginBottom": ".75rem"},
                required=f.get("required", False),
            )
        )

    schema_data = [
        {
            "Field": f["name"],
            "Type": f["type"],
            "Required": "Yes" if f.get("required") else "No",
        }
        for f in cmd["fields"]
    ]

    schema_table = dash_table.DataTable(
        id="schema-info-table",
        columns=[
            {"name": "Field", "id": "Field"},
            {"name": "Type", "id": "Type"},
            {"name": "Required", "id": "Required"},
        ],
        data=schema_data,
        style_table={"overflowX": "auto", "borderRadius": "var(--ox-radius)"},
        style_header={
            "backgroundColor": "var(--ox-bg-subtle)",
            "color": "var(--ox-text-secondary)",
            "fontWeight": "600",
            "padding": "8px 12px",
            "border": "none",
            "fontSize": ".78rem",
            "textTransform": "uppercase",
            "letterSpacing": ".04em",
        },
        style_cell={
            "textAlign": "left",
            "padding": "8px 12px",
            "fontFamily": "Inter, sans-serif",
            "fontSize": ".8rem",
            "border": "1px solid var(--ox-border-light)",
        },
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "var(--ox-bg-subtle)",
            },
            {
                "if": {"filter_query": "{Required} = Yes"},
                "backgroundColor": "#fefce8",
            },
        ],
    )

    schema_info = html.Div(
        [
            html.H4(cmd["name"], style={"color": "var(--ox-primary)"}),
            html.P(cmd.get("description", ""), style={"opacity": ".7", "marginBottom": "1rem"}),
            schema_table,
        ]
    )

    return form_fields, schema_info


@callback(
    Output("command-feedback", "children"),
    Output("json-array-feedback", "children"),
    Input("send-command-btn", "n_clicks"),
    Input("send-json-array-btn", "n_clicks"),
    State("command-type-dropdown", "value"),
    State("command-form-fields", "children"),
    State("command-json-array", "value"),
    prevent_initial_call=True,
)
def send_command(
    n_cmd: int | None,
    n_json: int | None,
    cmd_type: str,
    fields: list,
    json_array: str,
) -> tuple:
    """Dispatch a single command or a JSON batch."""
    import dash

    ctx = dash.callback_context
    if not ctx.triggered:
        return "", ""

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    ds = dash.get_app().data_service

    command_feedback = ""
    json_feedback = ""

    if trigger == "send-command-btn":
        payload: dict = {}
        for field in fields or []:
            fid = field["props"]["id"]
            fname = fid.replace("cmd_", "")
            fval = field["props"].get("value", "")

            cmd_def = next(
                (c for c in SAMPLE_COMMANDS if c["name"] == cmd_type),
                None,
            )
            if cmd_def:
                fd = next((f for f in cmd_def["fields"] if f["name"] == fname), None)
                if fd and fd["type"] == "number" and fval:
                    try:
                        fval = float(fval)
                    except ValueError:
                        pass
            payload[fname] = fval

        result = ds.dispatch_command(cmd_type, payload)
        if result["status"] == "success":
            command_feedback = html.Div(
                f"Command '{cmd_type}' dispatched successfully!",
                className="ox-alert ox-alert-success",
            )
        else:
            command_feedback = html.Div(
                f"Error: {result.get('message', 'unknown')}",
                className="ox-alert ox-alert-danger",
            )
        return command_feedback, json_feedback  # <-- FIX: was missing

    elif trigger == "send-json-array-btn":
        if not json_array or not json_array.strip():
            json_feedback = html.Div(
                "Please enter a JSON array",
                className="ox-alert ox-alert-warning",
            )
        else:
            try:
                arr = json.loads(json_array)
                if not isinstance(arr, list):
                    raise ValueError("Input must be a JSON array")
                ok = err = 0
                for item in arr:
                    if not isinstance(item, dict):
                        err += 1
                        continue
                    name = item.pop("command_type", SAMPLE_COMMANDS[0]["name"])
                    r = ds.dispatch_command(name, item)
                    if r["status"] == "success":
                        ok += 1
                    else:
                        err += 1
                if err == 0:
                    json_feedback = html.Div(
                        f"{ok} commands dispatched successfully!",
                        className="ox-alert ox-alert-success",
                    )
                else:
                    json_feedback = html.Div(
                        f"{ok} succeeded, {err} failed",
                        className="ox-alert ox-alert-warning",
                    )
            except (json.JSONDecodeError, ValueError) as exc:
                json_feedback = html.Div(
                    f"Invalid JSON: {exc}",
                    className="ox-alert ox-alert-danger",
                )
            except Exception as exc:
                json_feedback = html.Div(
                    f"Error: {exc}",
                    className="ox-alert ox-alert-danger",
                )

    return command_feedback, json_feedback

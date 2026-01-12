"""Command Center page for dispatching commands."""

from dash import html, dcc, callback, Output, Input, State
from dash.dependencies import ALL
import dash_bootstrap_components as dbc
import dash_table
import json

# Sample command schemas - in production, these would be discovered dynamically
SAMPLE_COMMANDS = [
    {
        "name": "CreateOrder",
        "description": "Create a new order",
        "fields": [
            {"name": "order_id", "label": "Order ID", "type": "text", "required": True},
            {"name": "customer_name", "label": "Customer Name", "type": "text", "required": True},
            {"name": "total_amount", "label": "Total Amount", "type": "number", "required": True},
        ]
    },
    {
        "name": "CancelOrder",
        "description": "Cancel an existing order",
        "fields": [
            {"name": "order_id", "label": "Order ID", "type": "text", "required": True},
        ]
    },
]

def command_center_page():
    """Create the command center page.

    Returns:
        Command center layout component
    """
    command_options = [
        {"label": f"{cmd['name']} - {cmd.get('description', '')}", "value": cmd["name"]}
        for cmd in SAMPLE_COMMANDS
    ]
    
    layout = html.Div([
        html.Div([
            html.H1("Command Center", className="dashboard-header"),
            html.P("Dispatch commands to the event-sourcing system", className="page-subtitle"),
        ], className="mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5([
                            html.I(className="bi bi-list-task me-2"),
                            "Predefined Processes"
                        ], className="mb-3"),
                        dbc.InputGroup([
                            dbc.InputGroupText([
                                html.I(className="bi bi-search")
                            ]),
                            dbc.Input(
                                id="process-search-input",
                                placeholder="Search processes...",
                                type="text",
                                className="mb-3"
                            ),
                        ], className="mb-3"),
                        html.Div(id="process-table-container"),
                        html.Div(id="process-execution-feedback"),
                    ])
                ], className="shadow-hover mb-4"),
            ], width=12),
        ], className="g-4 mb-4"),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5([
                            html.I(className="bi bi-send me-2"),
                            "Dispatch Command"
                        ], className="mb-3"),
                dbc.Form([
                            dbc.Label("Command Type", className="fw-bold"),
                    dcc.Dropdown(
                        options=command_options,
                        value=SAMPLE_COMMANDS[0]["name"],
                        id="command-type-dropdown",
                        clearable=False,
                        className="mb-3"
                    ),
                            html.Div(id="command-form-fields"),
                            dbc.Button([
                                html.I(className="bi bi-send-fill me-2"),
                                "Send Command"
                            ], color="primary", className="mt-3 w-100", id="send-command-btn"),
                    html.Div(id="command-feedback", className="mt-3"),
                        ]),
                    ])
                ], className="shadow-hover mb-4"),
                dbc.Card([
                    dbc.CardBody([
                        html.H5([
                            html.I(className="bi bi-code-slash me-2"),
                            "Batch Commands (JSON)"
                        ], className="mb-3"),
                        dbc.Label("JSON Array of Commands", className="fw-bold"),
                        dbc.Textarea(
                            id="command-json-array",
                            placeholder='[{"order_id": "123", "customer_name": "Alice", "total_amount": 99.99}]',
                            className="mb-3",
                            style={"minHeight": "120px", "fontFamily": "monospace"}
                        ),
                        dbc.Button([
                            html.I(className="bi bi-send-fill me-2"),
                            "Send JSON Array"
                        ], color="success", className="w-100", id="send-json-array-btn"),
                        html.Div(id="json-array-feedback", className="mt-3"),
                    ])
                ], className="shadow-hover"),
            ], width=12, lg=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H5([
                            html.I(className="bi bi-info-circle me-2"),
                            "Command Schemas"
                        ], className="mb-3"),
                        html.Div(id="command-schema-info"),
                    ])
                ], className="shadow-hover"),
            ], width=12, lg=6),
        ], className="g-4"),
    ], className="container-fluid")

    return layout


# Register callbacks at module level
@callback(
    Output("process-table-container", "children"),
    Input("process-table-container", "id"),  # Trigger on mount
    Input("process-search-input", "value"),
    prevent_initial_call=False
)
def render_process_table(_: str, search_text: str | None) -> html.Div:
        """Render process table.

        Args:
            _: Trigger ID (unused)
            search_text: Search text input

        Returns:
            Process table component
        """
        import dash
        try:
            process_service = dash.get_app().process_service  # type: ignore[attr-defined]
            processes = process_service.get_all_processes()
        except Exception:
            processes = []

        # Apply search filter
        if search_text:
            search_lower = search_text.lower()
            processes = [
                p for p in processes
                if search_lower in str(p.get("id", "")).lower()
                or search_lower in str(p.get("name", "")).lower()
                or search_lower in str(p.get("description", "")).lower()
                or search_lower in str(p.get("category", "")).lower()
            ]

        if not processes:
            return html.Div([
                html.I(className="bi bi-inbox me-2", style={"fontSize": "2rem"}),
                html.P("No processes available", className="mt-2 mb-0"),
                html.Small("Try adjusting your search", className="text-muted")
            ], className="text-center py-4")

        # Prepare data for DataTable
        table_data = []
        for proc in processes:
            proc_id = proc.get("id", "N/A")
            command_count = len(proc.get("command_sequence", []))
            table_data.append({
                "Process ID": proc_id,
                "Name": proc.get("name", "N/A"),
                "Description": proc.get("description", "N/A"),
                "Category": proc.get("category", "N/A"),
                "Commands": command_count,
                "Actions": proc_id,  # For button reference
            })

        # Define columns
        columns = [
            {"name": "Process ID", "id": "Process ID", "type": "text"},
            {"name": "Name", "id": "Name", "type": "text"},
            {"name": "Description", "id": "Description", "type": "text"},
            {"name": "Category", "id": "Category", "type": "text"},
            {"name": "Commands", "id": "Commands", "type": "numeric"},
            {"name": "Actions", "id": "Actions", "presentation": "markdown", "type": "text"},
        ]

        # Format Actions column with buttons (we'll use a workaround)
        for row in table_data:
            proc_id = row["Actions"]
            row["Actions"] = f"Execute"

        table = dash_table.DataTable(
            id="process-data-table",
            columns=columns,
            data=table_data,
            page_size=10,
            page_action="native",
            sort_action="native",
            filter_action="native",
            style_table={
                "overflowX": "auto",
                "borderRadius": "0.5rem",
            },
            style_header={
                "backgroundColor": "#00b894",
                "color": "white",
                "fontWeight": "bold",
                "textAlign": "left",
                "padding": "12px",
                "border": "none",
            },
            style_cell={
                "textAlign": "left",
                "padding": "10px",
                "fontFamily": "Inter, sans-serif",
                "fontSize": "0.875rem",
                "border": "1px solid #e8eaf6",
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
            ],
        )

        # Add execute buttons below table (workaround for DataTable button limitation)
        execute_buttons = html.Div([
            dbc.Button(
                [html.I(className="bi bi-play-fill me-1"), f"Execute {proc.get('id')}"],
                id={"type": "execute-process-btn", "index": proc.get("id")},
                color="success",
                size="sm",
                className="me-2 mb-2"
            )
            for proc in processes
        ], className="mt-3")

        return html.Div([
            table,
            html.Hr(),
            html.H6("Quick Actions:", className="mb-2"),
            execute_buttons
        ])


@callback(
    Output("process-execution-feedback", "children", allow_duplicate=True),
    Input({"type": "execute-process-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True
)
def execute_process(n_clicks_list: list[int | None]) -> html.Div:
        """Execute a process when button is clicked.

        Args:
            n_clicks_list: List of button click counts

        Returns:
            Feedback message
        """
        import dash
        
        ctx = dash.callback_context
        if not ctx.triggered:
            return html.Div()

        # Find which button was clicked
        button_id = ctx.triggered[0]["prop_id"]
        if "execute-process-btn" not in button_id:
            return html.Div()

        # Extract process ID from button ID
        try:
            import json
            button_data = json.loads(button_id.split(".")[0])
            process_id = button_data["index"]
        except Exception:
            return html.Div()

        try:
            app = dash.get_app()
            process_service = app.process_service  # type: ignore[attr-defined]
            data_service = app.data_service  # type: ignore[attr-defined]

            result = process_service.execute_process(process_id, data_service)

            if result["status"] == "success":
                return dbc.Alert([
                    html.I(className="bi bi-check-circle-fill me-2"),
                    html.Strong("Success: "),
                    result["message"],
                    html.Br(),
                    html.Small(f"Executed {len(result.get('executed_commands', []))} commands", className="text-muted")
                ], color="success", className="mt-3")
            elif result["status"] == "partial":
                return dbc.Alert([
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    html.Strong("Partial Success: "),
                    result["message"],
                    html.Br(),
                    html.Small(f"Errors: {', '.join(result.get('errors', []))}", className="text-danger")
                ], color="warning", className="mt-3")
            else:
                return dbc.Alert([
                    html.I(className="bi bi-x-circle-fill me-2"),
                    html.Strong("Error: "),
                    result.get("message", "Unknown error")
                ], color="danger", className="mt-3")
        except Exception as e:
            return dbc.Alert([
                html.I(className="bi bi-x-circle-fill me-2"),
                f"Error executing process: {str(e)}"
            ], color="danger", className="mt-3")


@callback(
    Output("command-form-fields", "children"),
    Output("command-schema-info", "children"),
    Input("command-type-dropdown", "value")
)
def update_form_fields(command_type: str) -> tuple:
        """Update form fields based on selected command type.

        Args:
            command_type: Selected command type

        Returns:
            Tuple of (form_fields, schema_info)
        """
        cmd = next((c for c in SAMPLE_COMMANDS if c["name"] == command_type), SAMPLE_COMMANDS[0])
    
        form_fields = []
        for field in cmd["fields"]:
            required_mark = " *" if field.get("required", False) else ""
            if field["type"] == "text":
                form_fields.append(
                    dbc.Input(
                        id=f"cmd_{field['name']}",
                        placeholder=field["label"] + required_mark,
                        type="text",
                        className="mb-3",
                        required=field.get("required", False)
                    )
                )
            elif field["type"] == "number":
                form_fields.append(
                    dbc.Input(
                        id=f"cmd_{field['name']}",
                        placeholder=field["label"] + required_mark,
                        type="number",
                        step="any",
                        className="mb-3",
                        required=field.get("required", False)
                    )
                )
    
        # Create schema info table
        schema_data = [
            {
                "Field": field["name"],
                "Label": field["label"],
                "Type": field["type"],
                "Required": "Yes" if field.get("required") else "No",
            }
            for field in cmd["fields"]
        ]
    
        schema_table = dash_table.DataTable(
            id="schema-info-table",
            columns=[
                {"name": "Field", "id": "Field", "type": "text"},
                {"name": "Label", "id": "Label", "type": "text"},
                {"name": "Type", "id": "Type", "type": "text"},
                {"name": "Required", "id": "Required", "type": "text"},
            ],
            data=schema_data,
            style_table={
                "overflowX": "auto",
                "borderRadius": "0.5rem",
            },
            style_header={
                "backgroundColor": "#4fc3f7",
                "color": "white",
                "fontWeight": "bold",
                "textAlign": "left",
                "padding": "8px",
                "border": "none",
            },
            style_cell={
                "textAlign": "left",
                "padding": "8px",
                "fontFamily": "Inter, sans-serif",
                "fontSize": "0.8rem",
                "border": "1px solid #e8eaf6",
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
                    "if": {"filter_query": "{Required} = Yes"},
                    "backgroundColor": "#fff3cd",
                },
            ],
        )

        schema_info = html.Div([
            html.H6(cmd["name"], className="text-primary mb-2"),
            html.P(cmd.get("description", ""), className="text-muted mb-3"),
            html.H6("Fields:", className="small fw-bold mb-2"),
            schema_table,
        ])
        
        return form_fields, schema_info


@callback(
    Output("command-feedback", "children"),
    Output("json-array-feedback", "children"),
    Input("send-command-btn", "n_clicks"),
    Input("send-json-array-btn", "n_clicks"),
    State("command-type-dropdown", "value"),
    State("command-form-fields", "children"),
    State("command-json-array", "value"),
    prevent_initial_call=True
)
def send_command(n_cmd: int | None, n_json: int | None, cmd_type: str, fields: list, json_array: str) -> tuple:
    """Handle command dispatch.

    Args:
        n_cmd: Send command button clicks
        n_json: Send JSON array button clicks
        cmd_type: Selected command type
        fields: Form field components
        json_array: JSON array string

    Returns:
        Tuple of (command_feedback, json_feedback)
    """
    import dash

    ctx = dash.callback_context
    if not ctx.triggered:
        return "", ""

    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    data_service = dash.get_app().data_service  # type: ignore[attr-defined]

    command_feedback = ""
    json_feedback = ""

    if trigger == "send-command-btn":
        # Single command from form
        payload = {}
        for field in fields:
            field_id = field["props"]["id"]
            field_name = field_id.replace("cmd_", "")
            field_value = field["props"].get("value", "")

            # Convert number fields
            cmd_def = next((c for c in SAMPLE_COMMANDS if c["name"] == cmd_type), None)
            if cmd_def:
                field_def = next((f for f in cmd_def["fields"] if f["name"] == field_name), None)
                if field_def and field_def["type"] == "number" and field_value:
                    try:
                        field_value = float(field_value)
                    except ValueError:
                        pass

            payload[field_name] = field_value

        result = data_service.dispatch_command(cmd_type, payload)
        if result["status"] == "success":
            command_feedback = dbc.Alert([
                html.I(className="bi bi-check-circle-fill me-2"),
                f"Command '{cmd_type}' dispatched successfully!"
            ], color="success", className="d-flex align-items-center")
        else:
                command_feedback = dbc.Alert([
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error: {result['message']}"
                ], color="danger", className="d-flex align-items-center")
        
    elif trigger == "send-json-array-btn":
        # Multiple commands as JSON array
        if not json_array or not json_array.strip():
            json_feedback = dbc.Alert("Please enter a JSON array", color="warning")
        else:
            try:
                arr = json.loads(json_array)
                if not isinstance(arr, list):
                    raise ValueError("Must be a JSON array")
                success_count = 0
                error_count = 0
                for item in arr:
                    if not isinstance(item, dict):
                        error_count += 1
                        continue
                    # Try to infer command type from data or use first available
                    cmd_name = item.pop("command_type", SAMPLE_COMMANDS[0]["name"])
                    result = data_service.dispatch_command(cmd_name, item)
                    if result["status"] == "success":
                        success_count += 1
                    else:
                        error_count += 1
                if error_count == 0:
                    json_feedback = dbc.Alert([
                        html.I(className="bi bi-check-circle-fill me-2"),
                        f"{success_count} commands dispatched successfully!"
                    ], color="success", className="d-flex align-items-center")
                else:
                    json_feedback = dbc.Alert([
                        html.I(className="bi bi-exclamation-triangle-fill me-2"),
                        f"{success_count} succeeded, {error_count} failed"
                    ], color="warning", className="d-flex align-items-center")
            except json.JSONDecodeError as e:
                json_feedback = dbc.Alert([
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Invalid JSON: {str(e)}"
                ], color="danger", className="d-flex align-items-center")
            except Exception as e:
                json_feedback = dbc.Alert([
                    html.I(className="bi bi-exclamation-triangle-fill me-2"),
                    f"Error: {str(e)}"
                ], color="danger", className="d-flex align-items-center")
        
        return command_feedback, json_feedback

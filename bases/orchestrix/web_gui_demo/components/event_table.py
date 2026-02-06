from dash import html


def event_table(events: list) -> html.Table:
    """Reusable table component for event lists with Notion-style design."""
    table_header = [html.Thead(html.Tr([html.Th("ID"), html.Th("Type"), html.Th("Payload")]))]
    table_body = [
        html.Tbody(
            [
                html.Tr([html.Td(evt["id"]), html.Td(evt["type"]), html.Td(str(evt["payload"]))])
                for evt in events
            ]
        )
    ]
    return html.Table(table_header + table_body, className="notion-table mb-4")

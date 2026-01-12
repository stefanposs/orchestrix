from .dashboard import dashboard_page, register_dashboard_callbacks
from .command_center import command_center_page
from .event_explorer import event_explorer_page
from .aggregate_viewer import aggregate_viewer_page, aggregate_details_page
# Optional: add processes page if implemented
try:
    from .processes import processes_page, process_details_page
except ImportError:
    processes_page = None
    process_details_page = None

PAGES = {
    "/": dashboard_page,
    "/commands": command_center_page,
    "/events": event_explorer_page,
    "/aggregates": aggregate_viewer_page,
}
## Processes page removed

# Add dynamic details route for aggregates
def aggregate_details_router(pathname):
    if pathname.startswith("/aggregates/") and aggregate_details_page:
        aggregate_id = pathname.split("/aggregates/")[-1]
        return aggregate_details_page(aggregate_id)
    return None
PAGES["/aggregates/<id>"] = aggregate_details_router

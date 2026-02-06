"""Page registry and dynamic routers."""

from .aggregate_viewer import aggregate_details_page, aggregate_viewer_page
from .command_center import command_center_page
from .dashboard import (
    dashboard_page,
)
from .dashboard import (
    register_dashboard_callbacks as register_dashboard_callbacks,
)
from .event_explorer import event_explorer_page

try:
    from .processes import process_details_page, processes_page
except ImportError:
    processes_page = None  # type: ignore[assignment]
    process_details_page = None  # type: ignore[assignment]

PAGES = {
    "/": dashboard_page,
    "/commands": command_center_page,
    "/events": event_explorer_page,
    "/aggregates": aggregate_viewer_page,
}

if processes_page is not None:
    PAGES["/processes"] = processes_page


def aggregate_details_router(pathname: str):
    """Route /aggregates/<id> to the details page."""
    if pathname.startswith("/aggregates/") and aggregate_details_page:
        aggregate_id = pathname.split("/aggregates/")[-1]
        return aggregate_details_page(aggregate_id)
    return None


PAGES["/aggregates/<id>"] = aggregate_details_router

if process_details_page is not None:

    def process_details_router(pathname: str):
        """Route /processes/<id> to the process details page."""
        if pathname.startswith("/processes/"):
            pid = pathname.split("/processes/")[-1]
            return process_details_page(pid)
        return None

    PAGES["/processes/<id>"] = process_details_router

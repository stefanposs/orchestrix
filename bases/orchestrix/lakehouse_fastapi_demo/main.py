"""Entrypoint for the lakehouse_demo FastAPI server (Polylith style)."""

from fastapi import FastAPI

from .handlers import get_router

app: FastAPI = FastAPI(title="Lakehouse Demo API")
app.include_router(get_router())


def start() -> None:
    """Start the FastAPI app using uvicorn. This is the entrypoint for the API."""
    import uvicorn

    # nosec S104: Binding to all interfaces is intended for local development/demo only. Safe to ignore ruff S104 here.
    uvicorn.run(
        "orchestrix.lakehouse_fastapi_demo.main:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=True,
    )

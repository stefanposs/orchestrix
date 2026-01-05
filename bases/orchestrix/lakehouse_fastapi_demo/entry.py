from fastapi import FastAPI
from orchestrix.lakehouse_demo.handlers import get_router


def main() -> None:
    """Entrypoint for running the Lakehouse FastAPI app (dev/demo only)."""
    import uvicorn

    app = FastAPI(title="Lakehouse Demo API")
    app.include_router(get_router())
    # S104: Binding to all interfaces is for dev/demo only
    # nosec S104: Binding to all interfaces is intended for local development/demo only. Safe to ignore ruff S104 here.
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)  # noqa: S104


if __name__ == "__main__":
    main()

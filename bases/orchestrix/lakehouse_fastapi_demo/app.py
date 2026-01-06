# ruff: noqa: I001
from fastapi import FastAPI
from .entry import router

app: FastAPI = FastAPI(
    title="Lakehouse Demo API",
    servers=[{"url": "http://0.0.0.0:8000", "description": "Default local dev server"}],
)
app.include_router(router)

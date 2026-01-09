"""Tests for CloudSQL event store implementation.

Uses pytest-asyncio for async tests and testcontainers for isolated PostgreSQL instances (Cloud SQL compatible).
"""

import warnings
import uuid
from dataclasses import dataclass

import pytest
from testcontainers.postgres import PostgresContainer

# Suppress known DeprecationWarnings from testcontainers and upb
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    message=r".*@wait_container_is_ready decorator is deprecated.*|.*Type google\._upb\._message.*",
)

pytest.importorskip("asyncpg", reason="asyncpg not installed - skip cloudsql tests")

from orchestrix.infrastructure.cloudsql import CloudSQLEventStore


@dataclass(frozen=True, kw_only=True)
class OrderCreated:
    order_id: str
    customer_id: str
    total: float


@pytest.fixture(scope="module")
def pg_container():
    """Start a PostgreSQL container for CloudSQL tests."""
    with PostgresContainer("postgres:15-alpine") as postgres:
        yield postgres


@pytest.fixture
def store(pg_container):
    """CloudSQL Event Store fixture, configured for the test container."""
    import os

    os.environ["GCP_SQL_HOST"] = pg_container.get_container_host_ip()
    os.environ["GCP_SQL_PORT"] = str(pg_container.get_exposed_port(5432))
    os.environ["GCP_SQL_DB"] = pg_container.dbname
    os.environ["GCP_SQL_USER"] = pg_container.username
    os.environ["GCP_SQL_PASSWORD"] = pg_container.password
    os.environ["GCP_SQL_SSLMODE"] = "disable"
    # Create schema
    import asyncpg
    import asyncio

    async def create_schema():
        conn = await asyncpg.connect(
            user=os.environ["GCP_SQL_USER"],
            password=os.environ["GCP_SQL_PASSWORD"],
            database=os.environ["GCP_SQL_DB"],
            host=os.environ["GCP_SQL_HOST"],
            port=int(os.environ["GCP_SQL_PORT"]),
            ssl=None,
        )
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            stream VARCHAR(255) NOT NULL,
            version INT NOT NULL,
            type VARCHAR(255) NOT NULL,
            data JSONB NOT NULL,
            timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_stream_version ON events(stream, version);
        """)
        await conn.close()

    asyncio.run(create_schema())
    return CloudSQLEventStore()


@pytest.mark.asyncio
async def test_append_and_load(store):
    stream = f"order-{uuid.uuid4()}"
    event = {"type": "OrderCreated", "data": {"order_id": "1", "customer_id": "c1", "total": 42.0}}
    await store.append(stream, event)
    events = [e async for e in store.load(stream)]
    assert len(events) == 1
    assert events[0]["type"] == "OrderCreated"
    assert events[0]["data"]["order_id"] == "1"


@pytest.mark.asyncio
async def test_query_by_type(store):
    stream = f"order-{uuid.uuid4()}"
    event = {"type": "OrderCreated", "data": {"order_id": "2", "customer_id": "c2", "total": 99.0}}
    await store.append(stream, event)
    found = [e async for e in store.query(type="OrderCreated")]
    assert any(e["data"]["order_id"] == "2" for e in found)

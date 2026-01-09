"""Google Cloud SQL (PostgreSQL) Event Store implementation for Orchestrix.

Implements the EventStore Protocol using asyncpg for PostgreSQL.

Configuration via .env or environment variables:
    GCP_SQL_HOST, GCP_SQL_PORT, GCP_SQL_DB, GCP_SQL_USER, GCP_SQL_PASSWORD, GCP_SQL_SSLMODE

Table schema (recommended):
    CREATE TABLE events (
        id SERIAL PRIMARY KEY,
        stream VARCHAR(255) NOT NULL,
        version INT NOT NULL,
        type VARCHAR(255) NOT NULL,
        data JSONB NOT NULL,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    CREATE UNIQUE INDEX idx_stream_version ON events(stream, version);
"""

import os
from collections.abc import AsyncIterator
import asyncpg


class CloudSQLEventStore:
    """Google Cloud SQL (PostgreSQL) implementation of the EventStore Protocol.

    Uses asyncpg for async database access.
    """

    def __init__(self):
        """Initialize the CloudSQLEventStore with connection pool as None."""
        self._pool = None
        self._dsn = self._build_dsn()

    async def append(self: "CloudSQLEventStore", stream: str, event: dict) -> None:
        """Append an event to a stream asynchronously."""
        await self._append_async(stream, event)

    async def load(
        self: "CloudSQLEventStore", stream: str, from_position: int = 0
    ) -> AsyncIterator[dict]:
        """Async generator: Load events from a stream starting at a given position."""
        async for event in self._load_async(stream, from_position):
            yield event

    def _build_dsn(self) -> str:
        """Build the PostgreSQL DSN from environment variables."""
        return (
            f"postgresql://{os.getenv('GCP_SQL_USER')}:{os.getenv('GCP_SQL_PASSWORD')}"
            f"@{os.getenv('GCP_SQL_HOST')}:{os.getenv('GCP_SQL_PORT', '5432')}"
            f"/{os.getenv('GCP_SQL_DB')}"
            f"?sslmode={os.getenv('GCP_SQL_SSLMODE', 'require')}"
        )

    async def initialize(self) -> None:
        """Initialize the asyncpg connection pool."""
        self._pool = await asyncpg.create_pool(dsn=self._dsn)

    async def _append_async(self, stream: str, event: dict) -> None:
        import json

        if self._pool is None:
            await self.initialize()
        async with self._pool.acquire() as conn:  # type: ignore[attr-defined]
            version = await conn.fetchval(
                "SELECT COALESCE(MAX(version), 0) + 1 FROM events WHERE stream = $1", stream
            )
            await conn.execute(
                """
                INSERT INTO events (stream, version, type, data)
                VALUES ($1, $2, $3, $4)
                """,
                stream,
                version,
                event["type"],
                json.dumps(event["data"]),
            )

    # (sync load entfernt, async load siehe oben)

    async def _load_async(self, stream: str, from_position: int = 0) -> AsyncIterator[dict]:
        if self._pool is None:
            await self.initialize()
        async with self._pool.acquire() as conn:  # type: ignore[attr-defined]
            rows = await conn.fetch(
                "SELECT version, type, data, timestamp FROM events WHERE stream = $1 AND version >= $2 ORDER BY version ASC",
                stream,
                from_position + 1,
            )
            import json

            for row in rows:
                data = row["data"]
                if isinstance(data, str):
                    data = json.loads(data)
                yield {
                    "version": row["version"],
                    "type": row["type"],
                    "data": data,
                    "timestamp": row["timestamp"],
                }

    async def query(self, **filters: object) -> AsyncIterator[dict]:
        """Async generator: Query events with optional filters."""
        if self._pool is None:
            await self.initialize()
        event_type = filters.get("type")
        async with self._pool.acquire() as conn:  # type: ignore[attr-defined]
            if event_type:
                rows = await conn.fetch(
                    "SELECT stream, version, type, data, timestamp FROM events WHERE type = $1 ORDER BY timestamp DESC",
                    event_type,
                )
            else:
                rows = await conn.fetch(
                    "SELECT stream, version, type, data, timestamp FROM events ORDER BY timestamp DESC"
                )
            import json

            for row in rows:
                data = row["data"]
                if isinstance(data, str):
                    data = json.loads(data)
                yield {
                    "stream": row["stream"],
                    "version": row["version"],
                    "type": row["type"],
                    "data": data,
                    "timestamp": row["timestamp"],
                }

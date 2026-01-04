"""PostgreSQL-based event store implementation using asyncpg.

This module provides a production-ready event store backed by PostgreSQL.
It uses asyncpg for async database operations and connection pooling.

Installation:
    pip install orchestrix[postgres]

Usage:
    from orchestrix.infrastructure import PostgreSQLEventStore

    store = PostgreSQLEventStore(
        connection_string="postgresql://user:pass@localhost/db"
    )
    await store.initialize()
    await store.save("aggregate-001", [event1, event2])
    events = await store.load("aggregate-001")
"""

from __future__ import annotations

import json
from dataclasses import dataclass, is_dataclass, asdict
from typing import Any
from decimal import Decimal
from datetime import datetime
from uuid import UUID

from orchestrix.core.event_store import EventStore
from orchestrix.core.exceptions import ConcurrencyError
from orchestrix.core.message import Event
from orchestrix.core.snapshot import Snapshot

class OrchestrixJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Decimal):
            return str(o)
        if isinstance(o, (datetime, UUID)):
            return str(o)
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)

try:
    import asyncpg
except ImportError as e:
    msg = (
        "PostgreSQL support requires asyncpg. "
        "Install with: pip install orchestrix[postgres]"
    )
    raise ImportError(msg) from e


@dataclass(frozen=True)
class PostgreSQLEventStore(EventStore):
    """PostgreSQL-backed event store with connection pooling.

    Provides ACID guarantees, optimistic concurrency control via version
    numbers, and efficient querying through PostgreSQL indexes.

    Attributes:
        connection_string: PostgreSQL connection string
        pool_min_size: Minimum number of connections in pool
        pool_max_size: Maximum number of connections in pool
        pool_timeout: Connection acquisition timeout in seconds
    """

    connection_string: str
    pool_min_size: int = 10
    pool_max_size: int = 50
    pool_timeout: float = 30.0
    _pool: asyncpg.Pool | None = None  # type: ignore[misc]

    def __post_init__(self) -> None:
        """Initialize connection pool placeholder."""
        # Use object.__setattr__ for frozen dataclass
        object.__setattr__(self, "_pool", None)

    async def initialize(self) -> None:
        """Create connection pool and ensure schema exists.

        Must be called before using the store. Creates the events
        and snapshots tables if they don't exist.
        """
        pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=self.pool_min_size,
            max_size=self.pool_max_size,
            timeout=self.pool_timeout,
        )
        object.__setattr__(self, "_pool", pool)
        await self._ensure_schema()

    async def close(self) -> None:
        """Close connection pool and release resources."""
        if self._pool is not None:
            await self._pool.close()
            object.__setattr__(self, "_pool", None)

    async def _ensure_schema(self) -> None:
        """Create tables and indexes if they don't exist."""
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            # Events table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id BIGSERIAL PRIMARY KEY,
                    aggregate_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    event_id TEXT NOT NULL UNIQUE,
                    event_type TEXT NOT NULL,
                    event_source TEXT NOT NULL,
                    event_subject TEXT,
                    event_data JSONB NOT NULL,
                    event_time TIMESTAMP WITH TIME ZONE NOT NULL,
                    spec_version TEXT,
                    data_content_type TEXT,
                    data_schema TEXT,
                    correlation_id TEXT,
                    causation_id TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    CONSTRAINT events_aggregate_version_unique
                        UNIQUE (aggregate_id, version)
                )
                """
            )

            # Indexes for performance
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_aggregate_id
                    ON events(aggregate_id)
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_type
                    ON events(event_type)
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_time
                    ON events(event_time DESC)
                """
            )
            await conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_events_correlation
                    ON events(correlation_id)
                    WHERE correlation_id IS NOT NULL
                """
            )

            # Snapshots table
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    aggregate_id TEXT PRIMARY KEY,
                    aggregate_type TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    state JSONB NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
                """
            )

    def save(self, aggregate_id: str, events: list[Event], expected_version: int | None = None) -> None:
        """Synchronous save not supported - use async version."""
        msg = "PostgreSQLEventStore requires async usage. Use await store.save(...)"
        raise NotImplementedError(msg)

    def load(
        self, aggregate_id: str, from_version: int | None = None
    ) -> list[Event]:
        """Synchronous load not supported - use async version."""
        msg = "PostgreSQLEventStore requires async usage. Use await store.load(...)"
        raise NotImplementedError(msg)

    async def save_async(
        self, aggregate_id: str, events: list[Event], expected_version: int | None = None
    ) -> None:
        """Save events to PostgreSQL with optimistic concurrency control.

        Args:
            aggregate_id: Unique identifier for the aggregate
            events: List of events to append to the stream
            expected_version: Expected current version for optimistic locking.
                If provided and doesn't match actual version, raises ConcurrencyError.

        Raises:
            ConcurrencyError: If expected_version doesn't match actual version
        """
        if not events:
            return

        assert self._pool is not None
        async with self._pool.acquire() as conn, conn.transaction():
            # Get current version
            current_version = await conn.fetchval(
                """
                SELECT COALESCE(MAX(version), -1)
                FROM events
                WHERE aggregate_id = $1
                """,
                aggregate_id,
            )

            # Check optimistic lock
            if expected_version is not None and current_version != expected_version:
                raise ConcurrencyError(
                    aggregate_id=aggregate_id,
                    expected_version=expected_version,
                    actual_version=current_version,
                )

            # Insert events with incremental versions
            try:
                for idx, event in enumerate(events):
                    version = current_version + idx + 1
                    await conn.execute(
                        """
                        INSERT INTO events (
                            aggregate_id, version, event_id, event_type,
                            event_source, event_subject, event_data, event_time,
                            spec_version, data_content_type, data_schema,
                            correlation_id, causation_id
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                        """,
                        aggregate_id,
                        version,
                        event.id,
                        event.type,
                        event.source,
                        event.subject,
                        json.dumps(self._event_to_dict(event), cls=OrchestrixJSONEncoder),
                        event.timestamp,
                        event.specversion,
                        event.datacontenttype,
                        event.dataschema,
                        event.correlation_id,
                        event.causation_id,
                    )
            except asyncpg.exceptions.UniqueViolationError as e:
                if "events_aggregate_version_unique" in str(e):
                    raise ConcurrencyError(
                        aggregate_id=aggregate_id,
                        expected_version=expected_version
                        if expected_version is not None
                        else current_version,
                        actual_version=current_version + 1,  # Approximate
                    ) from e
                raise

    async def load_async(
        self, aggregate_id: str, from_version: int | None = None
    ) -> list[Event]:
        """Load events from PostgreSQL for an aggregate.

        Args:
            aggregate_id: Unique identifier for the aggregate
            from_version: Optional version to start loading from

        Returns:
            List of events in chronological order
        """
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            if from_version is None:
                rows = await conn.fetch(
                    """
                    SELECT event_id, event_type, event_source, event_subject,
                           event_data, event_time, spec_version, data_content_type,
                           data_schema, correlation_id, causation_id
                    FROM events
                    WHERE aggregate_id = $1
                    ORDER BY version ASC
                    """,
                    aggregate_id,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT event_id, event_type, event_source, event_subject,
                           event_data, event_time, spec_version, data_content_type,
                           data_schema, correlation_id, causation_id
                    FROM events
                    WHERE aggregate_id = $1 AND version > $2
                    ORDER BY version ASC
                    """,
                    aggregate_id,
                    from_version,
                )

            return [self._row_to_event(row) for row in rows]

    def save_snapshot(self, snapshot: Snapshot) -> None:
        """Synchronous snapshot save not supported - use async version."""
        msg = "PostgreSQLEventStore requires async usage. Use await store.save_snapshot(...)"
        raise NotImplementedError(msg)

    def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        """Synchronous snapshot load not supported - use async version."""
        msg = "PostgreSQLEventStore requires async usage. Use await store.load_snapshot(...)"
        raise NotImplementedError(msg)

    async def save_snapshot_async(self, snapshot: Snapshot) -> None:
        """Save snapshot to PostgreSQL (upsert operation).

        Args:
            snapshot: Snapshot to save
        """
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO snapshots (aggregate_id, aggregate_type, version, state)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (aggregate_id)
                DO UPDATE SET
                    aggregate_type = EXCLUDED.aggregate_type,
                    version = EXCLUDED.version,
                    state = EXCLUDED.state,
                    created_at = NOW()
                """,
                snapshot.aggregate_id,
                snapshot.aggregate_type,
                snapshot.version,
                json.dumps(snapshot.state),
            )

    async def load_snapshot_async(self, aggregate_id: str) -> Snapshot | None:
        """Load latest snapshot from PostgreSQL.

        Args:
            aggregate_id: Unique identifier for the aggregate

        Returns:
            Latest snapshot if exists, None otherwise
        """
        assert self._pool is not None
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT aggregate_type, version, state
                FROM snapshots
                WHERE aggregate_id = $1
                """,
                aggregate_id,
            )

            if row is None:
                return None

            return Snapshot(
                aggregate_id=aggregate_id,
                aggregate_type=row["aggregate_type"],
                version=row["version"],
                state=json.loads(row["state"]),
            )

    async def ping(self) -> bool:
        """Check database connectivity.

        Returns:
            True if connection is healthy
        """
        if self._pool is None:
            return False
        try:
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
        except Exception:
            return False
        else:
            return True

    def _event_to_dict(self, event: Event) -> Any:
        """Convert Event to dictionary for JSON storage."""
        # Store all event fields except the CloudEvents metadata
        # which is stored in separate columns
        result = {
            key: value
            for key, value in vars(event).items()
            if key
            not in {
                "id",
                "type",
                "source",
                "subject",
                "timestamp",
                "specversion",
                "datacontenttype",
                "dataschema",
                "correlation_id",
                "causation_id",
                "data",
            }
        }

        # If event.data is present, handle it
        if event.data is not None:
            if not result:
                # If no other fields, return data directly (avoids nesting)
                return event.data
            elif isinstance(event.data, dict):
                # If data is a dict and we have other fields, merge them
                result.update(event.data)
            else:
                # If data is not a dict but we have other fields,
                # we must store it as 'data' key to preserve other fields
                result["data"] = event.data

        return result

    def _row_to_event(self, row: asyncpg.Record) -> Event:
        """Convert database row to Event object."""
        data = json.loads(row["event_data"]) if row["event_data"] else {}

        # Reconstruct Event from stored data
        return Event(
            id=row["event_id"],
            type=row["event_type"],
            source=row["event_source"],
            subject=row["event_subject"],
            timestamp=row["event_time"],
            datacontenttype=row["data_content_type"],
            dataschema=row["data_schema"],
            correlation_id=row["correlation_id"],
            causation_id=row["causation_id"],
            data=data,
        )

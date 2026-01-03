"""EventSourcingDB-based event store implementation using aiohttp.

This module provides a production-ready event store backed by EventSourcingDB.
It uses aiohttp for async HTTP operations and is CloudEvents-native.

Installation:
    pip install orchestrix[eventsourcingdb]

Usage:
    from orchestrix.infrastructure import EventSourcingDBStore

    store = EventSourcingDBStore(
        base_url="http://eventsourcingdb:3000",
        api_token="your-secret-token"
    )
    await store.save("aggregate-001", [event1, event2])
    events = await store.load("aggregate-001")
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from orchestrix.event_store import EventStore
from orchestrix.message import Event
from orchestrix.snapshot import Snapshot

try:
    import aiohttp
except ImportError as e:
    msg = (
        "EventSourcingDB support requires aiohttp. "
        "Install with: pip install orchestrix[eventsourcingdb]"
    )
    raise ImportError(msg) from e


@dataclass(frozen=True)
class EventSourcingDBStore(EventStore):
    """EventSourcingDB-backed event store with CloudEvents support.

    Provides native CloudEvents compatibility, built-in preconditions,
    and EventQL query language for complex read models.

    Attributes:
        base_url: EventSourcingDB base URL
        api_token: API token for authentication
        timeout: Request timeout in seconds
    """

    base_url: str
    api_token: str
    timeout: float = 30.0

    def __post_init__(self) -> None:
        """Initialize HTTP session placeholder."""
        object.__setattr__(self, "_session", None)

    async def initialize(self) -> None:
        """Create aiohttp session.

        Must be called before using the store.
        """
        session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_token}"},
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        )
        object.__setattr__(self, "_session", session)

    async def close(self) -> None:
        """Close aiohttp session and release resources."""
        if self._session is not None:
            await self._session.close()
            object.__setattr__(self, "_session", None)

    def save(self, aggregate_id: str, events: list[Event]) -> None:
        """Synchronous save not supported - use async version."""
        msg = "EventSourcingDBStore requires async usage. Use await store.save(...)"
        raise NotImplementedError(msg)

    def load(
        self, aggregate_id: str, from_version: int | None = None
    ) -> list[Event]:
        """Synchronous load not supported - use async version."""
        msg = "EventSourcingDBStore requires async usage. Use await store.load(...)"
        raise NotImplementedError(msg)

    async def save_async(self, aggregate_id: str, events: list[Event]) -> None:
        """Save events to EventSourcingDB.

        Args:
            aggregate_id: Unique identifier for the aggregate (maps to subject)
            events: List of events to append to the stream

        Raises:
            aiohttp.ClientError: On HTTP errors
        """
        if not events:
            return

        # Convert Orchestrix events to EventSourcingDB format
        event_candidates = [
            {
                "source": event.source,
                "subject": aggregate_id,  # Map aggregate_id to subject
                "type": event.type,
                "data": self._event_to_dict(event),
                "id": event.id,
                "time": event.timestamp.isoformat(),
                "specversion": event.specversion or "1.0",
                "datacontenttype": event.datacontenttype or "application/json",
                "dataschema": event.dataschema,
            }
            for event in events
        ]

        async with self._session.post(
            f"{self.base_url}/api/v1/write-events",
            json={"events": event_candidates},
        ) as response:
            response.raise_for_status()

    async def load_async(
        self, aggregate_id: str, from_version: int | None = None
    ) -> list[Event]:
        """Load events from EventSourcingDB for an aggregate.

        Args:
            aggregate_id: Unique identifier for the aggregate (maps to subject)
            from_version: Optional version to start loading from

        Returns:
            List of events in chronological order
        """
        # EventSourcingDB doesn't have explicit version numbers
        # but events are ordered chronologically
        async with self._session.post(
            f"{self.base_url}/api/v1/read-events",
            json={
                "subject": aggregate_id,
                "options": {"recursive": False},
            },
        ) as response:
            response.raise_for_status()

            events: list[Event] = []
            async for line in response.content:
                if not line:
                    continue

                # EventSourcingDB uses newline-delimited JSON streaming
                message = json.loads(line)

                # Skip heartbeat and stream control messages
                if message.get("type") in {"heartbeat", "stream-started"}:
                    continue

                # Handle errors
                if message.get("type") == "error":
                    error_msg = message.get("payload", {}).get("error", "Unknown error")
                    raise RuntimeError(f"EventSourcingDB error: {error_msg}")

                # Parse event
                if message.get("type") == "event":
                    payload = message.get("payload", {})
                    events.append(self._payload_to_event(payload))

            # Apply from_version filter if specified
            if from_version is not None and from_version >= 0:
                # Since EventSourcingDB doesn't expose version numbers,
                # we treat from_version as an index (0-based)
                events = events[from_version + 1 :]

            return events

    def save_snapshot(self, snapshot: Snapshot) -> None:
        """Synchronous snapshot save not supported - use async version."""
        msg = "EventSourcingDBStore requires async usage. Use await store.save_snapshot(...)"
        raise NotImplementedError(msg)

    def load_snapshot(self, aggregate_id: str) -> Snapshot | None:
        """Synchronous snapshot load not supported - use async version."""
        msg = "EventSourcingDBStore requires async usage. Use await store.load_snapshot(...)"
        raise NotImplementedError(msg)

    async def save_snapshot_async(self, snapshot: Snapshot) -> None:
        """Save snapshot as a special event to EventSourcingDB.

        EventSourcingDB treats snapshots as regular events with a special type.
        This aligns with Orchestrix's snapshot philosophy.

        Args:
            snapshot: Snapshot to save
        """
        snapshot_event = {
            "source": "orchestrix",
            "subject": snapshot.aggregate_id,
            "type": f"{snapshot.aggregate_type}.snapshot",
            "data": {
                "version": snapshot.version,
                "state": snapshot.state,
            },
            "specversion": "1.0",
            "datacontenttype": "application/json",
        }

        async with self._session.post(
            f"{self.base_url}/api/v1/write-events",
            json={"events": [snapshot_event]},
        ) as response:
            response.raise_for_status()

    async def load_snapshot_async(self, aggregate_id: str) -> Snapshot | None:
        """Load latest snapshot from EventSourcingDB.

        Uses EventSourcingDB's fromLatestEvent feature to find the
        most recent snapshot event.

        Args:
            aggregate_id: Unique identifier for the aggregate

        Returns:
            Latest snapshot if exists, None otherwise
        """
        # Query for snapshot events using EventQL
        query = f"""
            FROM e IN events
            WHERE e.subject = '{aggregate_id}'
              AND e.type LIKE '%.snapshot'
            ORDER BY e.time DESC
            LIMIT 1
            PROJECT INTO e
        """

        async with self._session.post(
            f"{self.base_url}/api/v1/run-eventql-query",
            json={"query": query},
        ) as response:
            if response.status == 404:
                return None

            response.raise_for_status()

            # Parse first result
            async for line in response.content:
                if not line:
                    continue

                message = json.loads(line)

                if message.get("type") == "row":
                    payload = message.get("payload", {})
                    data = payload.get("data", {})

                    # Extract aggregate type from event type
                    event_type = payload.get("type", "")
                    aggregate_type = event_type.replace(".snapshot", "")

                    return Snapshot(
                        aggregate_id=aggregate_id,
                        aggregate_type=aggregate_type,
                        version=data.get("version", 0),
                        state=data.get("state", {}),
                    )

            return None

    async def ping(self) -> bool:
        """Check EventSourcingDB connectivity.

        Returns:
            True if connection is healthy
        """
        try:
            async with self._session.get(
                f"{self.base_url}/api/v1/ping"
            ) as response:
                return response.status == 200
        except Exception:
            return False

    def _event_to_dict(self, event: Event) -> dict[str, Any]:
        """Convert Event to dictionary for storage.

        Excludes CloudEvents metadata fields which are stored separately.
        """
        return {
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
            }
        }

    def _payload_to_event(self, payload: dict[str, Any]) -> Event:
        """Convert EventSourcingDB payload to Orchestrix Event."""
        # Extract CloudEvents fields
        event_id = payload.get("id", "")
        event_type = payload.get("type", "")
        source = payload.get("source", "")
        subject = payload.get("subject")
        time_str = payload.get("time", "")
        specversion = payload.get("specversion", "1.0")
        datacontenttype = payload.get("datacontenttype", "application/json")
        dataschema = payload.get("dataschema")
        data = payload.get("data", {})

        # Parse timestamp
        timestamp = datetime.fromisoformat(time_str.replace("Z", "+00:00"))

        # Reconstruct Event
        return Event(
            id=event_id,
            type=event_type,
            source=source,
            subject=subject,
            timestamp=timestamp,
            specversion=specversion,
            datacontenttype=datacontenttype,
            dataschema=dataschema,
            **data,
        )

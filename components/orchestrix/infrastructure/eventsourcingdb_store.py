"""EventSourcingDB event store implementation using official Python SDK.

EventSourcingDB (https://www.eventsourcingdb.io) is a purpose-built database
for event sourcing with native CloudEvents support.

Features:
- CloudEvents-native storage (perfect alignment with Orchestrix)
- Built-in snapshots via events-as-snapshots pattern
- Preconditions for optimistic concurrency (IsSubjectPristine, IsSubjectOnEventId)
- EventQL query language for complex projections
- Single binary deployment (Docker/Kubernetes ready)
- Free tier: 25,000 events per instance per year

Installation:
    pip install orchestrix[eventsourcingdb]

Usage:
    from orchestrix.infrastructure import EventSourcingDBStore

    store = EventSourcingDBStore(
        base_url="http://localhost:2113",
        api_token="your-api-token",
    )
    await store.initialize()
    await store.save_async("order-123", events)

References:
    - Official SDK: https://pypi.org/project/eventsourcingdb/
    - Documentation: https://docs.eventsourcingdb.io/
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from orchestrix.core.event_store import EventStore
from orchestrix.core.message import Event
from orchestrix.core.snapshot import Snapshot

try:
    from eventsourcingdb import Client, ReadEventsOptions
except ImportError as e:
    msg = (
        "EventSourcingDB support requires official SDK. "
        "Install with: pip install orchestrix[eventsourcingdb]"
    )
    raise ImportError(msg) from e


@dataclass(frozen=True)
class EventSourcingDBStore(EventStore):
    """EventSourcingDB event store using official Python SDK.

    Stores events in EventSourcingDB with CloudEvents-native format.
    Uses subject field to map to aggregate_id.

    Attributes:
        base_url: EventSourcingDB base URL (e.g., http://localhost:2113)
        api_token: API token for authentication
    """

    base_url: str
    api_token: str
    _client: Client | None = None  # type: ignore[misc]

    def __post_init__(self) -> None:
        """Initialize client placeholder."""
        object.__setattr__(self, "_client", None)

    async def initialize(self) -> None:
        """Initialize EventSourcingDB client.

        Must be called before using the store.
        """
        client = Client(base_url=self.base_url, api_token=self.api_token)
        object.__setattr__(self, "_client", client)

    async def close(self) -> None:
        """Close client and release resources."""
        # SDK client doesn't require explicit cleanup
        object.__setattr__(self, "_client", None)

    def save(self, aggregate_id: str, events: list[Event], expected_version: int | None = None) -> None:
        """Synchronous save not supported - use async version."""
        msg = "EventSourcingDBStore requires async usage. Use await store.save_async(...)"
        raise NotImplementedError(msg)

    def load(
        self, aggregate_id: str, from_version: int | None = None
    ) -> list[Event]:
        """Synchronous load not supported - use async version."""
        msg = "EventSourcingDBStore requires async usage. Use await store.load_async(...)"
        raise NotImplementedError(msg)

    async def save_async(self, aggregate_id: str, events: list[Event], expected_version: int | None = None) -> None:
        """Save events to EventSourcingDB.

        Args:
            aggregate_id: Aggregate identifier (mapped to subject)
            events: List of events to save

        Raises:
            Exception: On SDK errors
        """
        if not events:
            return

        if self._client is None:
            await self.initialize()

        # Convert events to CloudEvents format for SDK
        event_dicts = []
        for event in events:
            cloud_event = {
                "source": event.source,
                "subject": event.subject or aggregate_id,
                "type": event.type,
                "data": self._serialize_event_data(event),
            }
            # Optional fields
            if event.id:
                cloud_event["id"] = event.id
            if event.timestamp:
                cloud_event["time"] = event.timestamp.isoformat()
            # CloudEvents spec_version (not part of base Event class)
            cloud_event["specversion"] = "1.0"
            if event.datacontenttype:
                cloud_event["datacontenttype"] = event.datacontenttype
            if event.dataschema:
                cloud_event["dataschema"] = event.dataschema

            event_dicts.append(cloud_event)

        # Write events using SDK
        assert self._client is not None
        await self._client.write_events(event_candidates=event_dicts)

    async def load_async(
        self, aggregate_id: str, from_version: int | None = None
    ) -> list[Event]:
        """Load events from EventSourcingDB.

        Args:
            aggregate_id: Aggregate identifier (mapped to subject)
            from_version: Optional starting version (1-based)

        Returns:
            List of events for the aggregate
        """
        if self._client is None:
            await self.initialize()

        # Read events using SDK
        events = []
        options = ReadEventsOptions(recursive=False)

        # Note: EventSourcingDB doesn't have built-in version filtering
        # We load all events and filter client-side if needed
        assert self._client is not None
        async for cloud_event in self._client.read_events(
            subject=aggregate_id, options=options
        ):
            event = self._deserialize_cloudevents(cloud_event, aggregate_id)
            events.append(event)

        if not events:
            raise ValueError(f"Aggregate {aggregate_id} not found")

        # Filter by version if requested
        if from_version is not None and events:
            # Version is implicit from order (1-based)
            events = events[from_version - 1 :]

        return events

    async def save_snapshot_async(self, snapshot: Snapshot) -> None:
        """Save snapshot as special event in EventSourcingDB.

        EventSourcingDB uses events-as-snapshots pattern:
        Snapshots are stored as special events with type suffix '.snapshot'

        Args:
            snapshot: Snapshot to save
        """
        if self._client is None:
            await self.initialize()

        # Create snapshot event
        snapshot_event: dict[str, Any] = {
            "source": "/snapshots",
            "subject": snapshot.aggregate_id,
            "type": f"{snapshot.aggregate_id}.snapshot",
            "data": {
                "aggregate_id": snapshot.aggregate_id,
                "version": snapshot.version,
                "state": snapshot.state,
            },
            "time": datetime.now(timezone.utc).isoformat(),
        }

        # Write snapshot using SDK
        await self._client.write_events(event_candidates=[snapshot_event])  # type: ignore[arg-type]

    async def load_snapshot_async(self, aggregate_id: str) -> Snapshot | None:
        """Load latest snapshot from EventSourcingDB.

        Uses EventQL to find the latest snapshot event.

        Args:
            aggregate_id: Aggregate identifier

        Returns:
            Latest snapshot or None if no snapshot exists
        """
        if self._client is None:
            await self.initialize()

        # EventQL query to find latest snapshot
        query = f"""
            FROM e IN events
            WHERE e.subject == "{aggregate_id}"
              AND e.type LIKE "%.snapshot"
            ORDER BY e.time DESC
            LIMIT 1
            PROJECT INTO e
        """

        # Execute EventQL query using SDK
        assert self._client is not None
        with contextlib.suppress(Exception):
            async for row in self._client.run_eventql_query(query=query):
                # Row is the projected event
                data = row.get("data", {})
                return Snapshot(
                    aggregate_id=data.get("aggregate_id", aggregate_id),
                    aggregate_type="",  # Not stored in EventQL result
                    version=data.get("version", 0),
                    state=data.get("state", {}),
                )

        return None

    async def ping(self) -> bool:
        """Check if EventSourcingDB is accessible.

        Returns:
            True if database is accessible, False otherwise
        """
        if self._client is None:
            return False

        try:
            await self._client.ping()
        except Exception:
            return False
        else:
            return True

    def _serialize_event_data(self, event: Event) -> dict:
        """Extract data field from event.

        Args:
            event: Orchestrix event

        Returns:
            Event data as dict
        """
        if hasattr(event.data, "__dict__"):
            # Dataclass or object with __dict__
            return vars(event.data)
        if isinstance(event.data, dict):
            return event.data
        # Primitive types
        return {"value": event.data}

    def _deserialize_cloudevents(
        self, cloud_event: object, aggregate_id: str
    ) -> Event:
        """Convert EventSourcingDB CloudEvent to Orchestrix Event.

        Args:
            cloud_event: CloudEvent from SDK (object or dict)
            aggregate_id: Aggregate identifier for fallback

        Returns:
            Orchestrix Event
        """
        # SDK may return event objects or dicts - handle both
        def get_value(obj: Any, key: str, default: Any = None) -> Any:
            """Get value from dict or object attribute."""
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)
        
        event_id = get_value(cloud_event, "id", "")
        event_type = get_value(cloud_event, "type", "")
        source = get_value(cloud_event, "source", "")
        subject = get_value(cloud_event, "subject", aggregate_id)
        data = get_value(cloud_event, "data", {})

        # Parse timestamp
        time_str = get_value(cloud_event, "time")
        if time_str:
            # Handle ISO format with Z or timezone
            timestamp = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        else:
            timestamp = datetime.now(timezone.utc)

        return Event(
            id=event_id,
            type=event_type,
            source=source,
            subject=subject,
            data=data,
            timestamp=timestamp,
            datacontenttype=get_value(cloud_event, "datacontenttype"),
            dataschema=get_value(cloud_event, "dataschema"),
            correlation_id=None,  # Not in CloudEvents standard
            causation_id=None,  # Not in CloudEvents standard
        )

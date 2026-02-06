"""Data service for accessing event store and aggregates."""

import json
from datetime import datetime
from typing import Any

from orchestrix.core.messaging.message import Command
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus
from orchestrix.infrastructure.memory.store import InMemoryEventStore


class DataService:
    """Service for querying event store and aggregates.

    Provides a clean interface for the GUI to access:
    - Events by aggregate ID
    - All aggregates
    - Event statistics
    - Command dispatch
    """

    def __init__(self, event_store: InMemoryEventStore, message_bus: InMemoryMessageBus) -> None:
        """Initialize data service.

        Args:
            event_store: The event store instance
            message_bus: The message bus for dispatching commands

        """
        self.event_store = event_store
        self.message_bus = message_bus

    def get_all_aggregate_ids(self) -> list[str]:
        """Get all aggregate IDs from the event store.

        Returns:
            List of aggregate IDs

        """
        if hasattr(self.event_store, "_events"):
            return list(self.event_store._events.keys())
        return []

    def get_events_for_aggregate(self, aggregate_id: str) -> list[dict[str, Any]]:
        """Get all events for an aggregate.

        Args:
            aggregate_id: The aggregate ID

        Returns:
            List of event dictionaries with serialized data

        """
        try:
            events = self.event_store.load(aggregate_id)
            return [
                {
                    "id": event.id,
                    "type": event.type,
                    "timestamp": (
                        event.timestamp.isoformat()
                        if isinstance(event.timestamp, datetime)
                        else str(event.timestamp)
                    ),
                    "data": self._serialize_data(event.data),
                    "trace_id": getattr(event, "trace_id", None),
                    "aggregate_id": aggregate_id,
                }
                for event in events
            ]
        except Exception:
            return []

    def get_all_events(self, limit: int = 1000) -> list[dict[str, Any]]:
        """Get all events across all aggregates.

        Args:
            limit: Maximum number of events to return

        Returns:
            List of event dictionaries

        """
        all_events = []
        for aggregate_id in self.get_all_aggregate_ids():
            events = self.get_events_for_aggregate(aggregate_id)
            all_events.extend(events)

        # Sort by timestamp descending
        all_events.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return all_events[:limit]

    def get_aggregate_summary(self, aggregate_id: str) -> dict[str, Any] | None:
        """Get summary information for an aggregate.

        Args:
            aggregate_id: The aggregate ID

        Returns:
            Dictionary with aggregate summary or None if not found

        """
        events = self.get_events_for_aggregate(aggregate_id)
        if not events:
            return None

        return {
            "id": aggregate_id,
            "event_count": len(events),
            "first_event": events[0] if events else None,
            "last_event": events[-1] if events else None,
            "version": len(events),
        }

    def get_all_aggregates_summary(self) -> list[dict[str, Any]]:
        """Get summary for all aggregates.

        Returns:
            List of aggregate summaries

        """
        summaries = []
        for aggregate_id in self.get_all_aggregate_ids():
            summary = self.get_aggregate_summary(aggregate_id)
            if summary:
                summaries.append(summary)
        return summaries

    def dispatch_command(self, command_type: str, data: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a command via the message bus.

        Args:
            command_type: The command type name
            data: Command payload data

        Returns:
            Result dictionary with status

        """
        try:
            command = Command(type=command_type, data=data)
            self.message_bus.publish(command)
            return {"status": "success", "message": f"Command {command_type} dispatched"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_event_statistics(self) -> dict[str, Any]:
        """Get statistics about events.

        Returns:
            Dictionary with event statistics

        """
        all_events = self.get_all_events(limit=10000)
        event_types: dict[str, int] = {}
        for event in all_events:
            event_type = event.get("type", "Unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

        return {
            "total_events": len(all_events),
            "total_aggregates": len(self.get_all_aggregate_ids()),
            "event_types": event_types,
        }

    def _serialize_data(self, data: object) -> str:
        """Serialize event data to JSON string.

        Args:
            data: The data to serialize

        Returns:
            JSON string representation

        """
        if data is None:
            return "{}"
        try:
            if isinstance(data, dict):
                return json.dumps(data, indent=2, default=str)
            return json.dumps({"value": data}, indent=2, default=str)
        except Exception:
            return str(data)

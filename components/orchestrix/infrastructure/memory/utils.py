"""Alias module for backward compatibility.

This module provides aliases for the infrastructure classes
to support the import pattern used in examples:
    from orchestrix.infrastructure.memory.utils import InMemoryEventStore, InMemoryMessageBus

The classes here provide _async method aliases for compatibility with examples.
"""

from collections.abc import Sequence

from orchestrix.core.eventsourcing.snapshot import Snapshot
from orchestrix.core.messaging.message import Event, Message
from orchestrix.infrastructure.memory.async_bus import InMemoryAsyncMessageBus
from orchestrix.infrastructure.memory.async_store import InMemoryAsyncEventStore


class InMemoryMessageBus(InMemoryAsyncMessageBus):
    """Message bus with _async method aliases for backward compatibility."""

    async def publish_async(self, message: Message) -> None:
        """Alias for publish() method."""
        return await self.publish(message)


class InMemoryEventStore(InMemoryAsyncEventStore):
    """Event store with _async method aliases for backward compatibility."""

    async def save_async(
        self, aggregate_id: str, events: Sequence[Event], expected_version: int | None = None
    ) -> None:
        """Alias for save() method."""
        return await self.save(aggregate_id, events, expected_version)

    async def load_async(self, aggregate_id: str, from_version: int = 0) -> list[Event]:
        """Alias for load() method."""
        return await self.load(aggregate_id, from_version)

    async def save_snapshot_async(self, snapshot: Snapshot) -> None:
        """Alias for save_snapshot() method."""
        return await self.save_snapshot(snapshot)

    async def load_snapshot_async(self, aggregate_id: str) -> Snapshot | None:
        """Alias for load_snapshot() method."""
        return await self.load_snapshot(aggregate_id)


__all__ = ["InMemoryEventStore", "InMemoryMessageBus"]

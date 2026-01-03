"""Orchestrix Infrastructure - Message Bus and Event Store implementations."""

from orchestrix.infrastructure.inmemory_bus import InMemoryMessageBus
from orchestrix.infrastructure.inmemory_store import InMemoryEventStore

# Optional imports with graceful fallback
try:
    from orchestrix.infrastructure.postgres_store import PostgreSQLEventStore
except ImportError:
    PostgreSQLEventStore = None  # type: ignore

try:
    from orchestrix.infrastructure.eventsourcingdb_store import EventSourcingDBStore
except ImportError:
    EventSourcingDBStore = None  # type: ignore

__all__ = [
    "InMemoryEventStore",
    "InMemoryMessageBus",
    "PostgreSQLEventStore",
    "EventSourcingDBStore",
]

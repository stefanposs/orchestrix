"""Orchestrix - A modular event-driven architecture framework."""

__path__ = __import__("pkgutil").extend_path(__path__, __name__)

from orchestrix.core.common import Module
from orchestrix.core.eventsourcing import AggregateRepository, AggregateRoot, EventStore
from orchestrix.core.messaging import (
    Command,
    CommandHandler,
    Event,
    Message,
    MessageBus,
)
from orchestrix.infrastructure.memory import InMemoryEventStore, InMemoryMessageBus

__all__ = [
    "AggregateRepository",
    "AggregateRoot",
    "Command",
    "CommandHandler",
    "Event",
    "EventStore",
    "InMemoryEventStore",
    "InMemoryMessageBus",
    "Message",
    "MessageBus",
    "Module",
]

__version__ = "0.1.0"

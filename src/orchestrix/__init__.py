"""Orchestrix - A modular event-driven architecture framework.

This package provides the core abstractions for building event-sourced applications
with CloudEvents-compatible messages.
"""

from orchestrix.command_handler import CommandHandler
from orchestrix.core.aggregate import AggregateRepository, AggregateRoot
from orchestrix.core.event import Event as CoreEvent
from orchestrix.event_store import EventStore
from orchestrix.infrastructure.inmemory_bus import InMemoryMessageBus
from orchestrix.infrastructure.inmemory_store import InMemoryEventStore
from orchestrix.message import Command, Event, Message
from orchestrix.message_bus import MessageBus
from orchestrix.module import Module

__all__ = [
    "AggregateRepository",
    "AggregateRoot",
    "Command",
    "CommandHandler",
    "CoreEvent",
    "Event",
    "EventStore",
    "InMemoryEventStore",
    "InMemoryMessageBus",
    "Message",
    "MessageBus",
    "Module",
]

__version__ = "0.1.0"

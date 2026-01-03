"""Core abstractions for event sourcing and CQRS.

This module provides the essential building blocks for event-sourced applications:
- AggregateRoot: Base class for domain aggregates
- AggregateRepository: Load and save aggregates with event replay
- Event: CloudEvents-compatible events
- MessageBus: Publish/subscribe messaging
"""

from orchestrix.core.aggregate import AggregateRepository, AggregateRoot
from orchestrix.core.message import Event
from orchestrix.core.messaging import MessageBus

__all__ = [
    "AggregateRepository",
    "AggregateRoot",
    "Event",
    "MessageBus",
]


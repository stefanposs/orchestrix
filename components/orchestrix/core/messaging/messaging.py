"""Messaging abstractions for event-driven communication.

This module re-exports the MessageBus protocol from the base orchestrix
package for convenient imports.
"""

from orchestrix.core.messaging.message_bus import MessageBus

__all__ = ["MessageBus"]

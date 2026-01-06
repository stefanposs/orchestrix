"""Message bus abstraction for Orchestrix.

The message bus handles command/event routing and delivery.
"""

from collections.abc import Callable, Coroutine
from typing import Any, Protocol, TypeVar

from orchestrix.core.messaging.message import Message

T = TypeVar("T", bound=Message)

MessageHandler = Callable[[Message], None]
AsyncMessageHandler = Callable[[Message], Coroutine[Any, Any, None]]


class MessageBus(Protocol):
    """Message bus for command and event routing.

    The bus is responsible for:
    - Routing commands to handlers
    - Publishing events to subscribers
    - Managing handler registration
    """

    def publish(self, message: Message) -> None:
        """Publish a message to all registered handlers.

        Args:
            message: The message to publish
        """
        ...

    def subscribe(self, message_type: type[T], handler: Callable[[T], None]) -> None:
        """Subscribe a handler to a message type.

        Args:
            message_type: The type of message to handle
            handler: The handler function
        """
        ...


class AsyncMessageBus(Protocol):
    """Async message bus for command and event routing.

    The bus is responsible for:
    - Routing commands to handlers
    - Publishing events to subscribers
    - Managing handler registration
    """

    async def publish(self, message: Message) -> None:
        """Publish a message to all registered handlers.

        Args:
            message: The message to publish
        """
        ...

    def subscribe(
        self, message_type: type[T], handler: Callable[[T], Coroutine[Any, Any, None]]
    ) -> None:
        """Subscribe a handler to a message type.

        Args:
            message_type: The type of message to handle
            handler: The handler function
        """
        ...

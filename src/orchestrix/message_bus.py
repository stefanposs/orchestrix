"""Message bus abstraction for Orchestrix.

The message bus handles command/event routing and delivery.
"""

from typing import Callable, Protocol

from orchestrix.message import Message

MessageHandler = Callable[[Message], None]


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

    def subscribe(self, message_type: type[Message], handler: MessageHandler) -> None:
        """Subscribe a handler to a message type.

        Args:
            message_type: The type of message to handle
            handler: The handler function
        """
        ...

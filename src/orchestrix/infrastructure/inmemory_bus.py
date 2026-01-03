"""In-memory message bus implementation.

Simple synchronous message bus for development and testing.
"""

from collections import defaultdict

from orchestrix.message import Message
from orchestrix.message_bus import MessageHandler


class InMemoryMessageBus:
    """In-memory synchronous message bus.

    Delivers messages immediately to all registered handlers.
    Suitable for development, testing, and single-process applications.
    """

    def __init__(self) -> None:
        self._handlers: dict[type[Message], list[MessageHandler]] = defaultdict(list)

    def publish(self, message: Message) -> None:
        """Publish a message to all registered handlers.

        Handlers are called synchronously in registration order.

        Args:
            message: The message to publish
        """
        message_type = type(message)
        for handler in self._handlers.get(message_type, []):
            handler(message)

    def subscribe(self, message_type: type[Message], handler: MessageHandler) -> None:
        """Subscribe a handler to a message type.

        Args:
            message_type: The type of message to handle
            handler: The handler function
        """
        self._handlers[message_type].append(handler)

"""In-memory message bus implementation.

Simple synchronous message bus for development and testing.
"""

from collections import defaultdict

from orchestrix.exceptions import HandlerError
from orchestrix.logging import StructuredLogger, get_logger
from orchestrix.message import Message
from orchestrix.message_bus import MessageHandler

_logger = StructuredLogger(get_logger(__name__))


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
        If a handler raises an exception, it is logged and other handlers continue.

        Args:
            message: The message to publish

        Raises:
            HandlerError: If all handlers fail (contains list of errors)
        """
        message_type = type(message)
        handlers = self._handlers.get(message_type, [])
        _logger.info(
            "Publishing message",
            message_type=message_type.__name__,
            message_id=message.id,
            handler_count=len(handlers),
        )

        errors: list[HandlerError] = []
        for handler in handlers:
            try:
                handler(message)
            except Exception as e:
                handler_name = getattr(handler, "__name__", handler.__class__.__name__)
                error = HandlerError(message_type.__name__, handler_name, e)
                errors.append(error)
                _logger.error(
                    "Handler failed",
                    message_type=message_type.__name__,
                    handler=handler_name,
                    error=str(e),
                )

        if errors and len(errors) == len(handlers):
            # All handlers failed - raise combined error
            raise HandlerError(
                message_type.__name__,
                "all_handlers",
                Exception(f"{len(errors)} handlers failed"),
            )

    def subscribe(self, message_type: type[Message], handler: MessageHandler) -> None:
        """Subscribe a handler to a message type.

        Args:
            message_type: The type of message to handle
            handler: The handler function
        """
        self._handlers[message_type].append(handler)
        _logger.debug("Handler subscribed", message_type=message_type.__name__)

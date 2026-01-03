"""Async message bus abstraction for Orchestrix.

Non-blocking message routing for async/await applications.
"""

import asyncio
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from orchestrix.core.exceptions import HandlerError
from orchestrix.core.logging import StructuredLogger, get_logger
from orchestrix.core.message import Message

# Type alias for async message handlers
AsyncMessageHandler = Callable[[Message], Coroutine[Any, Any, None]]

_logger = StructuredLogger(get_logger(__name__))


class InMemoryAsyncMessageBus:
    """In-memory async message bus.

    Routes messages to registered async handlers with concurrent execution.
    Multiple handlers for the same message type execute in parallel via asyncio.gather().

    Suitable for async applications, FastAPI, Starlette, and other async frameworks.
    """

    def __init__(self) -> None:
        """Initialize async message bus."""
        self._handlers: dict[type[Message], list[AsyncMessageHandler]] = defaultdict(
            list
        )

    async def publish(self, message: Message) -> None:
        """Publish a message to all registered async handlers.

        Handlers are called concurrently via asyncio.gather().
        If a handler raises an exception, it is logged and other handlers continue.
        If all handlers fail, raises HandlerError.

        Args:
            message: The message to publish

        Raises:
            HandlerError: If all handlers fail
        """
        message_type = type(message)
        handlers = self._handlers.get(message_type, [])

        _logger.info(
            "Publishing message (async)",
            message_type=message_type.__name__,
            message_id=getattr(message, "id", "N/A"),
            handler_count=len(handlers),
        )

        if not handlers:
            return

        # Create tasks for all handlers
        tasks = [handler(message) for handler in handlers]

        # Execute all handlers concurrently
        errors: list[HandlerError] = []
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check results for exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                handler = handlers[i]
                handler_name = getattr(handler, "__name__", handler.__class__.__name__)
                error = HandlerError(message_type.__name__, handler_name, result)
                errors.append(error)
                _logger.error(
                    "Async handler failed",
                    message_type=message_type.__name__,
                    handler=handler_name,
                    error=str(result),
                )

        # If all handlers failed, raise error
        if errors and len(errors) == len(handlers):
            raise HandlerError(
                message_type.__name__,
                "all_handlers",
                Exception(f"{len(errors)} handlers failed"),
            )

    def subscribe(
        self, message_type: type[Message], handler: AsyncMessageHandler
    ) -> None:
        """Subscribe an async handler to a message type.

        Args:
            message_type: The type of message to handle
            handler: The async handler function
        """
        self._handlers[message_type].append(handler)
        _logger.debug("Async handler subscribed", message_type=message_type.__name__)

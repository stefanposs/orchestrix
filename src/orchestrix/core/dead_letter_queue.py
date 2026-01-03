"""Dead letter queue for handling failed messages.

Messages that fail after max retries are routed to the dead letter queue
for later analysis and replay.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from orchestrix.core.message import Message


@dataclass(frozen=True)
class DeadLetteredMessage:
    """A message that failed and was routed to the dead letter queue.

    Attributes:
        message: The original message that failed
        reason: Why the message was dead lettered
        failure_count: Number of times handler failed
        timestamp: When the message was dead lettered
    """

    message: Message
    reason: str
    failure_count: int
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class DeadLetterQueue:
    """Protocol for dead letter queue implementations.

    Dead letter queues store messages that cannot be processed successfully.
    This allows for later analysis, debugging, and potential replay.
    """

    def enqueue(self, dead_lettered: DeadLetteredMessage) -> None:
        """Add a message to the dead letter queue.

        Args:
            dead_lettered: The dead lettered message to store
        """

    def dequeue_all(self) -> list[DeadLetteredMessage]:
        """Get all messages from the dead letter queue.

        Returns:
            List of all dead lettered messages
        """

    def clear(self) -> None:
        """Clear all messages from the dead letter queue."""

    def count(self) -> int:
        """Get the number of messages in the dead letter queue.

        Returns:
            Number of dead lettered messages
        """


class InMemoryDeadLetterQueue(DeadLetterQueue):
    """In-memory dead letter queue implementation.

    Stores failed messages in memory for development and testing.
    """

    def __init__(self) -> None:
        """Initialize the dead letter queue."""
        self._messages: list[DeadLetteredMessage] = []

    def enqueue(self, dead_lettered: DeadLetteredMessage) -> None:
        """Add a message to the dead letter queue.

        Args:
            dead_lettered: The dead lettered message to store
        """
        self._messages.append(dead_lettered)

    def dequeue_all(self) -> list[DeadLetteredMessage]:
        """Get all messages from the dead letter queue.

        Returns:
            List of all dead lettered messages (copy)
        """
        return list(self._messages)

    def clear(self) -> None:
        """Clear all messages from the dead letter queue."""
        self._messages.clear()

    def count(self) -> int:
        """Get the number of messages in the dead letter queue.

        Returns:
            Number of dead lettered messages
        """
        return len(self._messages)

    def get_by_message_id(self, message_id: str) -> DeadLetteredMessage | None:
        """Get a dead lettered message by its ID.

        Args:
            message_id: The ID of the original message

        Returns:
            The dead lettered message, or None if not found
        """
        for msg in self._messages:
            if msg.message.id == message_id:
                return msg
        return None

    def get_by_reason(self, reason: str) -> list[DeadLetteredMessage]:
        """Get all dead lettered messages with a specific reason.

        Args:
            reason: The failure reason to filter by

        Returns:
            List of dead lettered messages with matching reason
        """
        return [msg for msg in self._messages if msg.reason == reason]

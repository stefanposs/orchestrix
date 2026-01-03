"""Domain models for the notifications example."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from orchestrix.core.message import Command, Event


class NotificationChannel(str, Enum):
    """Notification delivery channels."""

    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationStatus(str, Enum):
    """Notification processing states."""

    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"


# Events


@dataclass(frozen=True, kw_only=True)
class UserRegistered(Event):
    """User registered in the system."""

    user_id: str
    email: str
    name: str
    registered_at: datetime


@dataclass(frozen=True, kw_only=True)
class OrderPlaced(Event):
    """Order was placed by user."""

    order_id: str
    user_id: str
    total_amount: float
    placed_at: datetime


@dataclass(frozen=True, kw_only=True)
class PaymentReceived(Event):
    """Payment was received."""

    payment_id: str
    order_id: str
    amount: float
    received_at: datetime


@dataclass(frozen=True, kw_only=True)
class NotificationRequested(Event):
    """Notification was requested."""

    notification_id: str
    channel: NotificationChannel
    recipient: str
    subject: str
    message: str
    metadata: dict
    requested_at: datetime


@dataclass(frozen=True, kw_only=True)
class NotificationSent(Event):
    """Notification was successfully sent."""

    notification_id: str
    channel: NotificationChannel
    recipient: str
    sent_at: datetime


@dataclass(frozen=True, kw_only=True)
class NotificationFailed(Event):
    """Notification failed to send."""

    notification_id: str
    channel: NotificationChannel
    recipient: str
    reason: str
    attempt: int
    failed_at: datetime


@dataclass(frozen=True, kw_only=True)
class NotificationRetrying(Event):
    """Notification is being retried."""

    notification_id: str
    attempt: int
    next_retry_at: datetime


@dataclass(frozen=True, kw_only=True)
class NotificationMovedToDeadLetter(Event):
    """Notification moved to dead letter queue after max retries."""

    notification_id: str
    channel: NotificationChannel
    recipient: str
    final_reason: str
    attempts: int
    moved_at: datetime


# Commands


@dataclass(frozen=True, kw_only=True)
class SendNotification(Command):
    """Send a notification."""

    notification_id: str
    channel: NotificationChannel
    recipient: str
    subject: str
    message: str
    metadata: dict | None = None

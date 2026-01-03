"""Notification handlers with retry logic and dead letter queue."""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from orchestrix.core.event import Event
from orchestrix.core.messaging import MessageBus

from .models import (
    NotificationChannel,
    NotificationFailed,
    NotificationMovedToDeadLetter,
    NotificationRequested,
    NotificationRetrying,
    NotificationSent,
    OrderPlaced,
    PaymentReceived,
    SendNotification,
    UserRegistered,
)


@dataclass
class RetryConfig:
    """Configuration for retry logic."""

    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0


@dataclass
class NotificationService:
    """Simulated notification service that can fail."""

    failure_rate: float = 0.3  # 30% failure rate for demo
    _send_count: int = field(default=0, init=False)

    async def send_email(self, recipient: str, subject: str, message: str) -> None:
        """Send an email (simulated)."""
        await asyncio.sleep(0.1)  # Simulate network delay
        self._send_count += 1

        # Simulate occasional failures
        if self._send_count % 3 == 0:  # Fail every 3rd attempt
            msg = "SMTP server timeout"
            raise ConnectionError(msg)

    async def send_sms(self, recipient: str, message: str) -> None:
        """Send an SMS (simulated)."""
        await asyncio.sleep(0.05)  # Simulate network delay
        self._send_count += 1

        if self._send_count % 4 == 0:  # Fail every 4th attempt
            msg = "SMS gateway error"
            raise ConnectionError(msg)

    async def send_push(self, recipient: str, subject: str, message: str) -> None:
        """Send a push notification (simulated)."""
        await asyncio.sleep(0.02)  # Simulate network delay
        # Push notifications always succeed for demo


@dataclass
class NotificationHandler:
    """Handler for notification events with retry logic."""

    message_bus: MessageBus
    notification_service: NotificationService
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    retry_attempts: dict[str, int] = field(default_factory=dict)
    dead_letter_queue: list[Event] = field(default_factory=list)

    async def handle_user_registered(self, event: Event) -> None:
        """Send welcome email when user registers."""
        data: UserRegistered = event.data

        # Create notification request
        now = datetime.now(timezone.utc)
        await self.message_bus.publish_async(
            NotificationRequested(
                notification_id=f"welcome-{data.user_id}",
                channel=NotificationChannel.EMAIL,
                recipient=data.email,
                subject="Welcome to Our Platform!",
                message=f"Hello {data.name},\\n\\nWelcome to our platform!",
                metadata={"user_id": data.user_id, "event": "registration"},
                requested_at=now,
            )
        )

    async def handle_order_placed(self, event: Event) -> None:
        """Send order confirmation when order is placed."""
        data: OrderPlaced = event.data

        now = datetime.now(timezone.utc)
        await self.message_bus.publish_async(
            NotificationRequested(
                notification_id=f"order-{data.order_id}",
                channel=NotificationChannel.EMAIL,
                recipient=f"user-{data.user_id}@example.com",  # Would lookup real email
                subject="Order Confirmation",
                message=f"Your order #{data.order_id} totaling ${data.total_amount} has been received.",
                metadata={"order_id": data.order_id, "event": "order_placed"},
                requested_at=now,
            )
        )

    async def handle_payment_received(self, event: Event) -> None:
        """Send payment receipt when payment is received."""
        data: PaymentReceived = event.data

        now = datetime.now(timezone.utc)
        await self.message_bus.publish_async(
            NotificationRequested(
                notification_id=f"payment-{data.payment_id}",
                channel=NotificationChannel.SMS,
                recipient="+1234567890",  # Would lookup real phone
                subject="Payment Received",
                message=f"Payment of ${data.amount} received for order {data.order_id}",
                metadata={"payment_id": data.payment_id, "event": "payment_received"},
                requested_at=now,
            )
        )

    async def handle_send_notification(self, command: SendNotification) -> None:
        """Send a notification with retry logic."""
        notification_id = command.notification_id
        attempt = self.retry_attempts.get(notification_id, 0) + 1
        self.retry_attempts[notification_id] = attempt

        try:
            # Attempt to send based on channel
            if command.channel == NotificationChannel.EMAIL:
                await self.notification_service.send_email(
                    recipient=command.recipient,
                    subject=command.subject,
                    message=command.message,
                )
            elif command.channel == NotificationChannel.SMS:
                await self.notification_service.send_sms(
                    recipient=command.recipient, message=command.message
                )
            elif command.channel == NotificationChannel.PUSH:
                await self.notification_service.send_push(
                    recipient=command.recipient,
                    subject=command.subject,
                    message=command.message,
                )

            # Success!
            now = datetime.now(timezone.utc)
            await self.message_bus.publish_async(
                NotificationSent(
                    notification_id=notification_id,
                    channel=command.channel,
                    recipient=command.recipient,
                    sent_at=now,
                )
            )

            # Clear retry counter
            self.retry_attempts.pop(notification_id, None)

        except Exception as e:
            now = datetime.now(timezone.utc)

            # Check if we should retry
            if attempt < self.retry_config.max_attempts:
                # Calculate retry delay with exponential backoff
                delay = min(
                    self.retry_config.initial_delay
                    * (self.retry_config.backoff_multiplier ** (attempt - 1)),
                    self.retry_config.max_delay,
                )

                next_retry = now + timedelta(seconds=delay)

                # Publish retry event
                await self.message_bus.publish_async(
                    NotificationRetrying(
                        notification_id=notification_id,
                        attempt=attempt,
                        next_retry_at=next_retry,
                    )
                )

                # Publish failed event
                await self.message_bus.publish_async(
                    NotificationFailed(
                        notification_id=notification_id,
                        channel=command.channel,
                        recipient=command.recipient,
                        reason=str(e),
                        attempt=attempt,
                        failed_at=now,
                    )
                )

                # Schedule retry
                await asyncio.sleep(delay)
                await self.message_bus.publish_async(command)

            else:
                # Max retries exceeded - move to dead letter queue
                await self.message_bus.publish_async(
                    NotificationMovedToDeadLetter(
                        notification_id=notification_id,
                        channel=command.channel,
                        recipient=command.recipient,
                        final_reason=str(e),
                        attempts=attempt,
                        moved_at=now,
                    )
                )

                # Store in dead letter queue for manual intervention
                self.dead_letter_queue.append(
                    Event.create(
                        event_type="DeadLetterNotification",
                        source="/notifications",
                        data={
                            "notification_id": notification_id,
                            "channel": command.channel,
                            "recipient": command.recipient,
                            "reason": str(e),
                            "attempts": attempt,
                        },
                    )
                )

                # Clear retry counter
                self.retry_attempts.pop(notification_id, None)


def register_handlers(
    message_bus: MessageBus,
    notification_service: NotificationService,
    retry_config: RetryConfig | None = None,
) -> NotificationHandler:
    """Register notification handlers with the message bus."""
    handler = NotificationHandler(
        message_bus=message_bus,
        notification_service=notification_service,
        retry_config=retry_config or RetryConfig(),
    )

    # Subscribe to domain events
    message_bus.subscribe(UserRegistered, handler.handle_user_registered)
    message_bus.subscribe(OrderPlaced, handler.handle_order_placed)
    message_bus.subscribe(PaymentReceived, handler.handle_payment_received)

    # Subscribe to commands
    message_bus.subscribe(SendNotification, handler.handle_send_notification)

    return handler

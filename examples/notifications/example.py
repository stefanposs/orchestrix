"""Complete notifications example with retry logic and dead letter queue."""
import asyncio
from datetime import datetime, timezone

from orchestrix.infrastructure.memory import InMemoryMessageBus

from .handlers import NotificationService, RetryConfig, register_handlers
from .models import OrderPlaced, PaymentReceived, UserRegistered


async def run_example() -> None:
    """Run the notifications example."""
    print("📬 Notifications Example with Retry Logic\n")
    print("=" * 70)

    # Setup
    message_bus = InMemoryMessageBus()
    notification_service = NotificationService()

    # Configure retry behavior
    retry_config = RetryConfig(
        max_attempts=3,
        initial_delay=0.5,  # Faster for demo
        backoff_multiplier=2.0,
        max_delay=5.0,
    )

    handler = register_handlers(message_bus, notification_service, retry_config)

    print("\n✅ Infrastructure initialized")
    print(f"   - Message Bus: {type(message_bus).__name__}")
    print(f"   - Notification Service: {type(notification_service).__name__}")
    print(f"   - Max Retry Attempts: {retry_config.max_attempts}")
    print(f"   - Initial Delay: {retry_config.initial_delay}s")
    print(f"   - Backoff Multiplier: {retry_config.backoff_multiplier}x")

    # Example 1: User Registration (Email)
    print("\n" + "=" * 70)
    print("Example 1: User Registration Notification (Email)")
    print("=" * 70)

    await message_bus.publish_async(
        UserRegistered(
            user_id="user-123",
            email="alice@example.com",
            name="Alice Johnson",
            registered_at=datetime.now(timezone.utc),
        )
    )

    print("\n📧 Sending welcome email to alice@example.com...")
    await asyncio.sleep(1.5)  # Wait for send + potential retry
    print("✅ Email sent successfully!")

    # Example 2: Order Placed (Email)
    print("\n" + "=" * 70)
    print("Example 2: Order Confirmation (Email)")
    print("=" * 70)

    await message_bus.publish_async(
        OrderPlaced(
            order_id="order-456",
            user_id="user-123",
            total_amount=149.99,
            placed_at=datetime.now(timezone.utc),
        )
    )

    print("\n📧 Sending order confirmation email...")
    await asyncio.sleep(1.5)
    print("✅ Confirmation sent!")

    # Example 3: Payment Received (SMS)
    print("\n" + "=" * 70)
    print("Example 3: Payment Receipt (SMS)")
    print("=" * 70)

    await message_bus.publish_async(
        PaymentReceived(
            payment_id="pay-789",
            order_id="order-456",
            amount=149.99,
            received_at=datetime.now(timezone.utc),
        )
    )

    print("\n📱 Sending payment receipt SMS...")
    await asyncio.sleep(1.5)
    print("✅ SMS sent!")

    # Example 4: Trigger more notifications to show retry logic
    print("\n" + "=" * 70)
    print("Example 4: Demonstrating Retry Logic")
    print("=" * 70)

    print("\n📬 Sending multiple notifications (some will fail and retry)...")

    # Send 5 more notifications
    for i in range(5):
        await message_bus.publish_async(
            UserRegistered(
                user_id=f"user-{200 + i}",
                email=f"user{200 + i}@example.com",
                name=f"User {200 + i}",
                registered_at=datetime.now(timezone.utc),
            )
        )

    # Wait for all sends and retries to complete
    await asyncio.sleep(3.0)

    # Show statistics
    print("\n" + "=" * 70)
    print("📊 Notification Statistics:")
    print("=" * 70)

    in_progress = len([a for a in handler.retry_attempts.values() if a < retry_config.max_attempts])
    failed = len(handler.dead_letter_queue)

    print(f"Total Send Attempts: {notification_service._send_count}")
    print(f"Active Retries: {in_progress}")
    print(f"Dead Letter Queue: {failed} notifications")

    if handler.retry_attempts:
        print("\nRetry Attempts by Notification:")
        for notif_id, attempts in handler.retry_attempts.items():
            status = "Retrying" if attempts < retry_config.max_attempts else "Failed"
            print(f"  - {notif_id}: {attempts} attempts ({status})")

    if handler.dead_letter_queue:
        print("\n💀 Dead Letter Queue Contents:")
        for event in handler.dead_letter_queue:
            print(f"  - {event.notification_id}")
            print(f"    Channel: {event.channel}")
            print(f"    Recipient: {event.recipient}")
            print(f"    Reason: {event.final_reason}")
            print(f"    Attempts: {event.attempts}")

    # Show retry configuration
    print("\n" + "=" * 70)
    print("⚙️  Retry Configuration:")
    print("=" * 70)
    print(f"Max Attempts: {retry_config.max_attempts}")
    print(f"Initial Delay: {retry_config.initial_delay}s")
    print(f"Backoff Multiplier: {retry_config.backoff_multiplier}x")
    print(f"Max Delay: {retry_config.max_delay}s")
    print("\nRetry Schedule:")
    for attempt in range(1, retry_config.max_attempts + 1):
        delay = min(
            retry_config.initial_delay * (retry_config.backoff_multiplier ** (attempt - 1)),
            retry_config.max_delay,
        )
        print(f"  Attempt {attempt}: {delay}s delay")

    print("\n✅ Example completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(run_example())

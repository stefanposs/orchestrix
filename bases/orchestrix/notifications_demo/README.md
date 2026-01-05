# Notifications Demo

This example demonstrates async event handlers with robust error handling,
retry logic, and dead letter queue pattern.

## Architecture

```
Domain Event (UserRegistered, OrderPlaced, PaymentReceived)
    ↓
Event Handler → NotificationRequested
    ↓
SendNotification Command
    ↓
Notification Service (can fail)
    ↓
    ├─ Success → NotificationSent
    ├─ Failure → NotificationFailed → Retry (with exponential backoff)
    └─ Max Retries → NotificationMovedToDeadLetter
```

## Retry Logic

Exponential backoff strategy:
- Attempt 1: Immediate
- Attempt 2: 1 second delay
- Attempt 3: 2 seconds delay
- Max attempts: 3 (configurable)
- Max delay: 60 seconds

## Dead Letter Queue

Failed notifications after max retries are moved to a dead letter queue for:
- Manual investigation
- Alert admins
- Retry with manual intervention
- Audit trail of failures

## Usage

```python
import asyncio
from datetime import datetime, timezone

from orchestrix.infrastructure.memory import InMemoryMessageBus

from examples.notifications.handlers import (
    NotificationService,
    RetryConfig,
    register_handlers,
)
from examples.notifications.models import UserRegistered


async def main():
    # Setup
    message_bus = InMemoryMessageBus()
    notification_service = NotificationService(failure_rate=0.3)

    # Configure retry behavior
    retry_config = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        backoff_multiplier=2.0,
        max_delay=60.0,
    )

    handler = register_handlers(message_bus, notification_service, retry_config)

    # Trigger notification
    await message_bus.publish_async(
        UserRegistered(
            user_id="user-123",
            email="alice@example.com",
            name="Alice",
            registered_at=datetime.now(timezone.utc),
        )
    )

    # Give time for retries
    await asyncio.sleep(5)

    # Check dead letter queue
    print(f"Failed notifications: {len(handler.dead_letter_queue)}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Patterns

### 1. Retry with Exponential Backoff
Automatic retry with increasing delays:
```python
delay = initial_delay * (backoff_multiplier ** (attempt - 1))
delay = min(delay, max_delay)  # Cap at maximum

await asyncio.sleep(delay)
await message_bus.publish_async(command)  # Retry
```

### 2. Dead Letter Queue
Failed messages after max retries:
```python
if attempt >= max_attempts:
    # Move to dead letter queue
    dead_letter_queue.append(event)

    # Alert admins
    await send_admin_alert(notification_id, reason)

    # Log for investigation
    logger.error(f"Notification {notification_id} moved to DLQ")
```

### 3. Async Event Handlers
Multiple handlers can process same event:
```python
# Handler 1: Send email
message_bus.subscribe(OrderPlaced, send_email_handler)

# Handler 2: Send SMS
message_bus.subscribe(OrderPlaced, send_sms_handler)

# Handler 3: Update metrics
message_bus.subscribe(OrderPlaced, metrics_handler)
```

### 4. Handler Pipeline
Chain of handlers processing notifications:
```python
1. Validation Handler → Validate recipient format
2. Rate Limiting Handler → Check rate limits
3. Enrichment Handler → Add user preferences
4. Sending Handler → Actually send notification
5. Tracking Handler → Track delivery metrics
```

## Notification Channels

**Email:**
- Subject and body
- HTML/plain text
- Attachments support

**SMS:**
- Short text messages
- Character limits
- Delivery receipts

**Push Notifications:**
- Mobile app notifications
- Badge counts
- Deep linking

**Webhooks:**
- HTTP callbacks
- Retry logic
- Signature verification

## Production Considerations

1. **Rate Limiting**: Prevent notification spam
   ```python
   @dataclass
   class RateLimiter:
       max_per_minute: int = 100
       window: dict = field(default_factory=dict)

       async def check_limit(self, user_id: str) -> bool:
           # Implementation
           pass
   ```

2. **Idempotency**: Prevent duplicate sends
   ```python
   sent_notifications = set()

   if notification_id in sent_notifications:
       return  # Already sent

   await send_notification(...)
   sent_notifications.add(notification_id)
   ```

3. **Circuit Breaker**: Stop sending when service is down
   ```python
   @dataclass
   class CircuitBreaker:
       failure_threshold: int = 5
       timeout: float = 60.0
       state: str = "closed"  # closed, open, half-open

       async def call(self, func, *args, **kwargs):
           if self.state == "open":
               raise ServiceUnavailable()
           # Implementation
   ```

4. **Monitoring**: Track notification metrics
   - Success rate per channel
   - Average retry attempts
   - Dead letter queue size
   - Delivery time percentiles

5. **User Preferences**: Respect notification settings
   ```python
   preferences = await get_user_preferences(user_id)

   if not preferences.email_enabled:
       return  # Don't send

   if preferences.quiet_hours:
       await schedule_for_later(notification)
   ```

6. **Template Management**: Centralize message templates
   ```python
   templates = {
       "welcome": "Hello {name}, welcome to {platform}!",
       "order_confirm": "Order #{order_id} confirmed",
   }

   message = templates["welcome"].format(
       name=user.name,
       platform="MyApp",
   )
   ```

## Testing

```python
async def test_retry_logic():
    # Setup
    message_bus = InMemoryMessageBus()
    service = NotificationService()
    config = RetryConfig(max_attempts=3, initial_delay=0.1)
    handler = register_handlers(message_bus, service, config)

    # Simulate failure
    service.failure_rate = 1.0  # Always fail

    # Send notification
    await message_bus.publish_async(
        SendNotification(
            notification_id="test-1",
            channel=NotificationChannel.EMAIL,
            recipient="test@example.com",
            subject="Test",
            message="Test message",
        )
    )

    # Wait for retries
    await asyncio.sleep(1.0)

    # Verify moved to dead letter queue
    assert len(handler.dead_letter_queue) == 1
    assert handler.retry_attempts.get("test-1") is None  # Cleared


async def test_exponential_backoff():
    config = RetryConfig(
        initial_delay=1.0,
        backoff_multiplier=2.0,
        max_delay=60.0,
    )

    # Attempt 1: 1.0 seconds
    # Attempt 2: 2.0 seconds
    # Attempt 3: 4.0 seconds
    # Attempt 4: 8.0 seconds (capped at 60.0)
```

## Monitoring Dashboard

Track notification health:

```
Notification Dashboard
─────────────────────
Total Sent:     10,542
Success Rate:   98.5%
Failed:         158
In DLQ:         12
Avg Retry:      1.3

By Channel:
  Email:  7,234 (98.2% success)
  SMS:    2,108 (99.1% success)
  Push:   1,200 (100% success)

Recent Failures:
  1. SMTP timeout - user-456@example.com
  2. SMS gateway error - +1234567890
  3. Invalid email format - invalid@@example.com
```
"""

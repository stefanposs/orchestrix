# Notifications: Retry Logic and Dead Letter Queue

This example demonstrates async event handlers with robust error handling, retry logic with exponential backoff, and the dead letter queue pattern.

> **📂 Source Code:**  
> Complete Example: [`examples/notifications/`](https://github.com/stefanposs/orchestrix/tree/main/examples/notifications)  
> Main Demo: [`examples/notifications/example.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/notifications/example.py)  
> Domain Models: [`examples/notifications/models.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/notifications/models.py)

## Overview

The notifications example demonstrates:

- ✅ **Retry Logic** - Exponential backoff for transient failures
- ✅ **Dead Letter Queue** - Handle permanent failures
- ✅ **Multiple Channels** - Email, SMS, Push, Webhooks
- ✅ **Circuit Breaker** - Protect against cascading failures
- ✅ **Async Event Handlers** - Non-blocking notification processing

## Quick Start

```bash
# Run the notifications demo
uv run python bases/orchestrix/notifications/example.py
```

## Architecture

Notification flow with automatic retry and DLQ:

```
Domain Event (UserRegistered, OrderPlaced, PaymentReceived)
    ↓
Event Handler → NotificationRequested
    ↓
SendNotification Command
    ↓
Notification Service (can fail)
    ↓
    ├─ Success → NotificationSent ✅
    ├─ Transient Failure → Retry (exponential backoff) 🔄
    └─ Max Retries Exceeded → NotificationMovedToDeadLetter ❌
```

## Retry Strategy

Exponential backoff with configurable parameters:

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0  # seconds

# Retry schedule:
# Attempt 1: Immediate
# Attempt 2: 1.0 second delay
# Attempt 3: 2.0 seconds delay
# Attempt 4: 4.0 seconds delay (if max_attempts=4)
```

## Dead Letter Queue

Failed notifications after max retries are moved to DLQ for:

- 🔍 **Manual Investigation** - Review failure reasons
- 🚨 **Alert Admins** - Notify operations team
- 🔄 **Manual Retry** - Retry with intervention
- 📊 **Audit Trail** - Track all failures

## Domain Model

### Commands

#### SendNotification
```python
@dataclass(frozen=True, kw_only=True)
class SendNotification(Command):
    notification_id: str
    channel: NotificationChannel  # EMAIL, SMS, PUSH, WEBHOOK
    recipient: str
    subject: Optional[str] = None
    message: str
    metadata: dict = field(default_factory=dict)

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
```

### Events

**Domain Events (trigger notifications):**
- `UserRegistered` - Welcome email
- `OrderPlaced` - Order confirmation
- `OrderShipped` - Shipping notification
- `PaymentReceived` - Payment receipt

**Notification Events:**
- `NotificationRequested` - Notification triggered
- `NotificationSent` - Successfully delivered
- `NotificationFailed` - Delivery failed (with retry info)
- `NotificationMovedToDeadLetter` - Max retries exceeded

## Key Patterns

### 1. Retry with Exponential Backoff

Automatic retry with increasing delays to handle transient failures:

```python
class NotificationHandler:
    def __init__(self, config: RetryConfig):
        self.config = config
        self.retry_attempts = {}
    
    async def send_notification(self, command: SendNotification):
        notification_id = command.notification_id
        attempt = self.retry_attempts.get(notification_id, 1)
        
        try:
            # Attempt to send
            await self.service.send(command)
            
            # Success - clear retry tracking
            self.retry_attempts.pop(notification_id, None)
            
        except TransientError as e:
            # Retry with backoff
            if attempt < self.config.max_attempts:
                delay = self.calculate_delay(attempt)
                await asyncio.sleep(delay)
                
                self.retry_attempts[notification_id] = attempt + 1
                await self.send_notification(command)  # Retry
            else:
                # Max retries exceeded - move to DLQ
                await self.move_to_dlq(notification_id, str(e))
    
    def calculate_delay(self, attempt: int) -> float:
        delay = self.config.initial_delay * (
            self.config.backoff_multiplier ** (attempt - 1)
        )
        return min(delay, self.config.max_delay)
```

### 2. Dead Letter Queue

Store failed messages for manual intervention:

```python
@dataclass
class DeadLetterMessage:
    notification_id: str
    command: SendNotification
    failure_reason: str
    attempts: int
    first_failure: datetime
    last_failure: datetime

class NotificationHandler:
    dead_letter_queue: list[DeadLetterMessage] = []
    
    async def move_to_dlq(
        self,
        notification_id: str,
        reason: str,
    ):
        message = DeadLetterMessage(
            notification_id=notification_id,
            command=self.pending[notification_id],
            failure_reason=reason,
            attempts=self.retry_attempts[notification_id],
            first_failure=self.first_attempts[notification_id],
            last_failure=datetime.now(),
        )
        
        self.dead_letter_queue.append(message)
        
        # Alert admins
        await self.send_admin_alert(
            f"Notification {notification_id} moved to DLQ: {reason}"
        )
        
        # Log for investigation
        logger.error(
            f"DLQ: {notification_id} failed after "
            f"{message.attempts} attempts"
        )
```

### 3. Async Event Handlers

Multiple handlers can process the same event:

```python
# Handler 1: Send email notification
@message_bus.subscribe(OrderPlaced)
async def send_email_notification(event: OrderPlaced):
    await message_bus.send(SendNotification(
        notification_id=f"email-{event.order_id}",
        channel=NotificationChannel.EMAIL,
        recipient=event.customer_email,
        subject=f"Order Confirmation: {event.order_id}",
        message=f"Your order has been placed...",
    ))

# Handler 2: Send SMS notification
@message_bus.subscribe(OrderPlaced)
async def send_sms_notification(event: OrderPlaced):
    await message_bus.send(SendNotification(
        notification_id=f"sms-{event.order_id}",
        channel=NotificationChannel.SMS,
        recipient=event.customer_phone,
        message=f"Order {event.order_id} confirmed!",
    ))

# Handler 3: Update metrics
@message_bus.subscribe(OrderPlaced)
async def update_metrics(event: OrderPlaced):
    metrics["orders_placed"].inc()
```

### 4. Circuit Breaker

Prevent cascading failures when notification service is down:

```python
@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    timeout: float = 60.0  # seconds
    state: str = "closed"  # closed, open, half-open
    failure_count: int = 0
    last_failure: Optional[datetime] = None
    
    async def call(self, func, *args, **kwargs):
        if self.state == "open":
            if self.should_attempt_reset():
                self.state = "half-open"
            else:
                raise ServiceUnavailable("Circuit breaker is open")
        
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        self.failure_count = 0
        self.state = "closed"
    
    def on_failure(self):
        self.failure_count += 1
        self.last_failure = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
    
    def should_attempt_reset(self) -> bool:
        if self.last_failure is None:
            return False
        
        elapsed = (datetime.now() - self.last_failure).total_seconds()
        return elapsed >= self.timeout
```

## Usage Example

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
    
    # Simulate unreliable service (30% failure rate)
    notification_service = NotificationService(failure_rate=0.3)

    # Configure retry behavior
    retry_config = RetryConfig(
        max_attempts=3,
        initial_delay=1.0,
        backoff_multiplier=2.0,
        max_delay=60.0,
    )

    # Register handlers
    handler = register_handlers(
        message_bus,
        notification_service,
        retry_config
    )

    # Trigger notification
    await message_bus.publish_async(
        UserRegistered(
            user_id="user-123",
            email="alice@example.com",
            name="Alice",
            registered_at=datetime.now(timezone.utc),
        )
    )

    # Wait for retries to complete
    await asyncio.sleep(5)

    # Check results
    print(f"Sent: {len(handler.sent_notifications)}")
    print(f"Failed (in DLQ): {len(handler.dead_letter_queue)}")
    
    # Process dead letter queue
    for dlq_message in handler.dead_letter_queue:
        print(f"DLQ: {dlq_message.notification_id}")
        print(f"  Reason: {dlq_message.failure_reason}")
        print(f"  Attempts: {dlq_message.attempts}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Notification Channels

### Email
```python
await send_notification(
    channel=NotificationChannel.EMAIL,
    recipient="user@example.com",
    subject="Welcome to Our Platform!",
    message="<html><body>Welcome Alice...</body></html>",
    metadata={"template": "welcome", "lang": "en"},
)
```

### SMS
```python
await send_notification(
    channel=NotificationChannel.SMS,
    recipient="+1234567890",
    message="Your verification code is: 123456",
    metadata={"country_code": "US"},
)
```

### Push Notifications
```python
await send_notification(
    channel=NotificationChannel.PUSH,
    recipient="device-token-abc123",
    message="You have a new message!",
    metadata={
        "badge": 1,
        "sound": "default",
        "deep_link": "/messages/123",
    },
)
```

### Webhooks
```python
await send_notification(
    channel=NotificationChannel.WEBHOOK,
    recipient="https://api.partner.com/webhook",
    message=json.dumps({"event": "order.placed", "order_id": "123"}),
    metadata={"signature": "hmac-sha256..."},
)
```

## Testing

### Test Retry Logic

```python
async def test_retry_with_eventual_success():
    # Setup service that fails first 2 attempts, succeeds on 3rd
    service = NotificationService(fail_count=2)
    config = RetryConfig(max_attempts=3, initial_delay=0.1)
    handler = NotificationHandler(service, config)
    
    # Send notification
    await handler.send_notification(SendNotification(
        notification_id="test-1",
        channel=NotificationChannel.EMAIL,
        recipient="test@example.com",
        message="Test",
    ))
    
    # Wait for retries
    await asyncio.sleep(0.5)
    
    # Verify succeeded on 3rd attempt
    assert len(handler.sent_notifications) == 1
    assert len(handler.dead_letter_queue) == 0
```

### Test Dead Letter Queue

```python
async def test_move_to_dlq_after_max_retries():
    # Setup service that always fails
    service = NotificationService(failure_rate=1.0)
    config = RetryConfig(max_attempts=3, initial_delay=0.1)
    handler = NotificationHandler(service, config)
    
    # Send notification
    await handler.send_notification(SendNotification(
        notification_id="test-1",
        channel=NotificationChannel.EMAIL,
        recipient="test@example.com",
        message="Test",
    ))
    
    # Wait for retries
    await asyncio.sleep(1.0)
    
    # Verify moved to DLQ after 3 attempts
    assert len(handler.sent_notifications) == 0
    assert len(handler.dead_letter_queue) == 1
    assert handler.dead_letter_queue[0].attempts == 3
```

### Test Exponential Backoff

```python
async def test_exponential_backoff_timing():
    config = RetryConfig(
        initial_delay=1.0,
        backoff_multiplier=2.0,
        max_delay=60.0,
    )
    handler = NotificationHandler(None, config)
    
    # Verify delay calculations
    assert handler.calculate_delay(1) == 1.0   # 1.0 * 2^0
    assert handler.calculate_delay(2) == 2.0   # 1.0 * 2^1
    assert handler.calculate_delay(3) == 4.0   # 1.0 * 2^2
    assert handler.calculate_delay(4) == 8.0   # 1.0 * 2^3
    assert handler.calculate_delay(10) == 60.0 # Capped at max_delay
```

## Production Considerations

### 1. Rate Limiting

Prevent notification spam:

```python
@dataclass
class RateLimiter:
    max_per_minute: int = 100
    window: dict = field(default_factory=dict)

    async def check_limit(self, user_id: str) -> bool:
        now = datetime.now()
        minute_key = now.replace(second=0, microsecond=0)
        
        if minute_key not in self.window:
            self.window = {minute_key: {}}
        
        count = self.window[minute_key].get(user_id, 0)
        
        if count >= self.max_per_minute:
            return False  # Rate limit exceeded
        
        self.window[minute_key][user_id] = count + 1
        return True
```

### 2. Idempotency

Prevent duplicate sends:

```python
sent_notifications = set()

async def send_notification(command: SendNotification):
    if command.notification_id in sent_notifications:
        return  # Already sent
    
    await notification_service.send(command)
    sent_notifications.add(command.notification_id)
```

### 3. User Preferences

Respect notification settings:

```python
preferences = await get_user_preferences(user_id)

if not preferences.email_enabled:
    return  # User disabled email notifications

if preferences.quiet_hours:
    if is_quiet_hour(datetime.now()):
        await schedule_for_later(notification)
        return
```

### 4. Monitoring

Track notification health:

```python
metrics = {
    "notifications_sent": Counter(),
    "notifications_failed": Counter(),
    "notifications_in_dlq": Gauge(),
    "retry_attempts": Histogram(),
    "delivery_time": Histogram(),
}

# Usage
with metrics["delivery_time"].time():
    await send_notification(command)

metrics["notifications_sent"].inc()
```

### 5. Template Management

Centralize message templates:

```python
templates = {
    "welcome": {
        "subject": "Welcome to {platform}!",
        "body": "Hello {name}, thank you for joining...",
    },
    "order_confirm": {
        "subject": "Order #{order_id} Confirmed",
        "body": "Your order has been placed...",
    },
}

message = templates["welcome"]["body"].format(
    name=user.name,
    platform="MyApp",
)
```

## Related Examples

- **[E-Commerce](ecommerce.md)** - Trigger notifications from order events
- **[Banking](banking.md)** - Send transaction notifications
- **[Lakehouse GDPR](lakehouse-gdpr.md)** - Compliance notifications

## Learn More

- [Async Handlers Guide](../guide/message-bus.md#async-handlers)
- [Error Handling](../guide/best-practices.md#error-handling)
- [Testing Async Code](../development/testing.md)

## Source Code

- [`handlers.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/notifications/handlers.py) - Retry logic and DLQ implementation
- [`models.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/notifications/models.py) - Commands and events
- [`example.py`](https://github.com/stefanposs/orchestrix/blob/main/examples/notifications/example.py) - Complete demo

[**Browse Complete Example →**](https://github.com/stefanposs/orchestrix/tree/main/examples/notifications)

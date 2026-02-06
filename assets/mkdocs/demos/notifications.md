
# Notifications Demo — Retry Logic & Dead Letter Queue

Resilient notification system with configurable retry policies, exponential backoff,
multi-channel delivery (email, SMS, push, webhook), and dead letter queue handling.

> **Source Code:**
> [`bases/orchestrix/notifications_demo/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/notifications_demo)

## Quick Start

```bash
uv run python -m bases.orchestrix.notifications_demo.main
```

## What It Demonstrates

- **Multi-channel delivery** — email, SMS, push, webhook
- **Retry with exponential backoff** — configurable `RetryConfig`
- **Dead letter queue** — permanent failures captured for review
- **Event-driven triggers** — domain events spawn notification commands
- **Notification lifecycle** — PENDING → SENDING → SENT / FAILED / DEAD_LETTER

## Domain Model

### Command

| Command | Fields |
|---|---|
| `SendNotification` | `notification_id`, `channel`, `recipient`, `subject`, `message`, `metadata` |

### Events

| Event | Description |
|---|---|
| `UserRegistered` | Triggers welcome notification |
| `OrderPlaced` | Triggers order confirmation |
| `PaymentReceived` | Triggers payment receipt |
| `NotificationRequested` | Notification queued |
| `NotificationSent` | Delivery succeeded |
| `NotificationFailed` | Delivery failed |
| `NotificationRetrying` | Retry scheduled |
| `NotificationMovedToDeadLetter` | Moved to DLQ after max retries |

### Channels

```python
class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
```

## Retry Strategy

```python
@dataclass
class RetryConfig:
    max_attempts: int = 3
    initial_delay: float = 1.0       # seconds
    backoff_multiplier: float = 2.0
    max_delay: float = 60.0          # seconds
```

| Attempt | Delay |
|---|---|
| 1 | immediate |
| 2 | 1.0 s |
| 3 | 2.0 s |
| 4 | 4.0 s (if max_attempts ≥ 4) |

## Code Structure

```
bases/orchestrix/notifications_demo/
├── main.py       # Runnable entry point (async demo)
├── models.py     # Commands, Events, Enums
├── handlers.py   # NotificationHandler with retry + DLQ logic
└── README.md
```

## Related

- [Banking Demo](banking.md) — Saga pattern with compensation
- [E-Commerce Demo](ecommerce.md) — Multi-step order processing
- [Best Practices](../guide/best-practices.md) — Error handling patterns

# Notifications Demo

Resilient notification system demonstrating retry policies, dead letter queues, and multi-channel delivery with Orchestrix.

## What It Demonstrates
- **Retry Policies**: Exponential backoff, fixed delay, linear backoff
- **Dead Letter Queue**: Failed messages captured for inspection and replay
- **Multi-Channel**: Email, SMS, push notification handlers
- **Event-Driven**: Notifications triggered by domain events

## Running

```bash
uv run python -m bases.orchestrix.notifications_demo.main
```

## Key Files
| File | Purpose |
|------|---------|
| `bases/orchestrix/notifications_demo/models.py` | Commands & Events for notification delivery |
| `bases/orchestrix/notifications_demo/handlers.py` | Channel-specific handlers with retry logic |
| `bases/orchestrix/notifications_demo/main.py` | Runnable entry point with DLQ demonstration |

## Architecture
All domain logic lives in `bases/orchestrix/notifications_demo/`. This project assembly is a thin deployment wrapper following the Polylith pattern.
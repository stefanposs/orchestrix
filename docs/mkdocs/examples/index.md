# Examples

Orchestrix comes with production-ready examples demonstrating real-world patterns and best practices for event-driven architectures.

## Available Examples

### 🏦 [Banking](banking.md)
Account management system with event sourcing, including:

- Account creation and transactions
- Event-driven balance updates
- Transaction history and audit trail
- Domain-driven design patterns

**Key Concepts:** Event Sourcing, Aggregates, Domain Events  
**Source:** [`examples/banking/`](https://github.com/stefanposs/orchestrix/tree/main/examples/banking)  
**Run:** `uv run python -m examples.banking.example`

---

### 🛒 [E-Commerce](ecommerce.md)
Complete order processing system with:

- Order lifecycle management
- Saga pattern for distributed transactions
- Payment processing coordination
- Inventory management integration

**Key Concepts:** Sagas, Process Managers, Event Choreography  
**Source:** [`examples/ecommerce/`](https://github.com/stefanposs/orchestrix/tree/main/examples/ecommerce)  
**Run:** `uv run python -m examples.ecommerce.example`

---

### 🏢 [Lakehouse Platform](lakehouse-gdpr.md)
Data lakehouse with GDPR compliance featuring:

- **[GDPR Compliance](lakehouse-gdpr.md)** - Right-to-be-forgotten implementation
- Data Anonymization - 8 anonymization strategies
- Event sourcing for audit trails
- Snapshot optimization for large event streams

**Key Concepts:** GDPR Compliance, Data Anonymization, Event Store, Snapshots  
**Source:** [`examples/lakehouse/`](https://github.com/stefanposs/orchestrix/tree/main/examples/lakehouse)  
**Quick Start:**
- Anonymization: `uv run python -m examples.lakehouse.example`
- GDPR Demo: `uv run python examples/lakehouse/gdpr_simple.py`

---

### 🔔 [Notifications](notifications.md)
Resilient notification system with:

- Retry logic with exponential backoff
- Dead letter queue for failed messages
- Email, SMS, and push notification channels
- Circuit breaker pattern

**Key Concepts:** Resilience Patterns, Dead Letter Queue, Retries  
**Source:** [`examples/notifications/`](https://github.com/stefanposs/orchestrix/tree/main/examples/notifications)  
**Run:** `uv run python -m examples.notifications.example`

---

## Running Examples

All examples are located in the `examples/` directory and can be run directly:

```bash
# Banking example
uv run python -m examples.banking.example

# E-Commerce example  
uv run python -m examples.ecommerce.example

# Lakehouse anonymization
uv run python -m examples.lakehouse.example

# Lakehouse GDPR compliance
uv run python examples/lakehouse/gdpr_simple.py

# Notifications example
uv run python -m examples.notifications.example
```

## Example Structure

Each example follows a consistent structure:

```
examples/
├── {domain}/
│   ├── README.md              # Overview and quick start
│   ├── __init__.py            # Module exports
│   ├── models.py              # Commands, Events, Domain models
│   ├── aggregate.py           # Aggregate root with business logic
│   ├── handlers.py            # Command and event handlers
│   ├── saga.py                # Saga orchestration (if applicable)
│   └── example.py             # Runnable demo
```

## Learning Path

### 1. **Start with Banking**
Learn the fundamentals of event sourcing and aggregates with a simple domain.

### 2. **Move to E-Commerce**
Understand sagas and process managers for coordinating distributed transactions.

### 3. **Study Lakehouse**
See production patterns for compliance, data management, and advanced event sourcing.

### 4. **Explore Notifications**
Master resilience patterns, retries, and error handling.

## Common Patterns

All examples demonstrate these key patterns:

### Event Sourcing
```python
class OrderAggregate(AggregateRoot):
    def handle_create_order(self, cmd: CreateOrder):
        event = OrderCreated(order_id=cmd.order_id, ...)
        self._apply_event(event)
    
    def _when_order_created(self, event: OrderCreated):
        self.order_id = event.order_id
        self.status = OrderStatus.PENDING
```

### Command/Event Separation
```python
# Command (intent)
@dataclass(frozen=True)
class CreateOrder(Command):
    order_id: str
    customer_id: str

# Event (fact)
@dataclass(frozen=True)
class OrderCreated(Event):
    order_id: str
    customer_id: str
    timestamp: datetime
```

### Saga Pattern
```python
async def on_order_created(event: OrderCreated, bus: MessageBus):
    # Step 1: Reserve inventory
    await bus.send(ReserveInventory(order_id=event.order_id))
    
    # Step 2: Process payment
    await bus.send(ProcessPayment(order_id=event.order_id))
```

## Next Steps

- **[Getting Started](../getting-started/quick-start.md)** - Build your first module
- **[Core Concepts](../getting-started/concepts.md)** - Understand the framework
- **[API Reference](../api/core.md)** - Detailed API documentation
- **[Best Practices](../guide/best-practices.md)** - Production guidelines

## Contributing Examples

Have a great example? Contributions are welcome! See our [Contributing Guide](../development/contributing.md).

Examples should:

- ✅ Demonstrate a real-world use case
- ✅ Follow consistent structure
- ✅ Include comprehensive README
- ✅ Be fully runnable
- ✅ Show best practices
- ✅ Include inline documentation

# Commands & Events

Commands and events are the two main message types in Orchestrix. Understand the difference!

## Commands vs Events

| Aspect | Command | Event |
|--------|---------|-------|
| **Meaning** | Intention (what should happen) | Fact (what has happened) |
| **Tense** | Imperative (CreateOrder) | Past (OrderCreated) |
| **Handler** | Exactly 1 handler | 0 to N handlers |
| **Validation** | Can be rejected | Has already happened |
| **Source** | Application/User | Domain Logic |

## Commands

### Definition

**A Command** represents an **intention to change state**.

```python
from dataclasses import dataclass
from orchestrix import Command

@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    """Command to create a new order."""
    order_id: str
    customer_id: str
    items: list[dict]
    shipping_address: str
```

### Naming Convention

- **Imperative**: CreateX, UpdateX, DeleteX, CancelX
- **Specific**: What exactly should happen?
- **Domain Language**: Terms from the business domain

```python
# ✅ Good
class PlaceOrder(Command): pass
class CancelSubscription(Command): pass
class ApproveInvoice(Command): pass

# ❌ Bad
class OrderCommand(Command): pass  # Too generic
class DoSomething(Command): pass   # Not meaningful
class Process(Command): pass       # What is processed?
```

### Command Design

```python
@dataclass(frozen=True, kw_only=True)
class RegisterUser(Command):
    """Register a new user account.
    
    Business Rules:
    - Email must be unique
    - Password min 8 characters
    - Username alphanumeric only
    """
    user_id: str
    email: str
    username: str
    password: str
    terms_accepted: bool = False
    
    def __post_init__(self) -> None:
        """Validate command data."""
        if not self.terms_accepted:
            raise ValueError("Terms must be accepted")
        if len(self.password) < 8:
            raise ValueError("Password too short")
```

## Events

### Definition

**An Event** represents a **fact that has already happened**.

```python
from dataclasses import dataclass
from orchestrix import Event

@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    """Event emitted when an order is successfully created."""
    order_id: str
    customer_id: str
    total_amount: float
    created_at: str
```

### Naming Convention

- **Past tense**: XCreated, XUpdated, XDeleted, XCancelled
- **Fact**: What actually happened?
- **Domain Events**: Business-relevant events

```python
# ✅ Good
class OrderPlaced(Event): pass
class SubscriptionCancelled(Event): pass
class InvoiceApproved(Event): pass
class PaymentReceived(Event): pass

# ❌ Bad
class OrderEvent(Event): pass     # Too generic
class OrderChange(Event): pass    # What changed?
class Updated(Event): pass        # What was updated?
```

### Event Design

Events should be **immutable** and **serializable**:

```python
@dataclass(frozen=True, kw_only=True)
class UserRegistered(Event):
    """User successfully registered.
    
    Downstream consumers:
    - Email service: Send welcome email
    - Analytics: Track new user
    - Billing: Create customer account
    """
    user_id: str
    email: str
    username: str
    registered_at: str
    referral_code: str | None = None
    
    # ❌ No mutable objects!
    # settings: dict  # Better: own dataclass
    
    # ✅ Immutable data
    # settings: UserSettings  # Own frozen dataclass
```

## Message Flow

```
┌─────────────┐
│   Client    │
└──────┬──────┘
    │
    │ publish(Command)
    ▼
┌──────────────────┐
│   MessageBus     │
└──────┬───────────┘
    │
    │ route to handler
    ▼
┌──────────────────┐      ┌─────────────┐
│ CommandHandler   │─────▶│  Aggregate  │
└──────┬───────────┘      └──────┬──────┘
    │                         │
    │                         │ emit Events
    │                         ▼
    │                  ┌──────────────┐
    │                  │ OrderCreated │
    │                  │ ItemAdded    │
    │                  └──────┬───────┘
    │                         │
    │ save & publish          │
    ▼                         │
┌──────────────────┐             │
│   EventStore     │◀────────────┘
└──────┬───────────┘
    │
    │ publish Events
    ▼
┌──────────────────────────┐
│   Event Handlers         │
│   - EmailService         │
│   - Analytics            │
│   - InventoryService     │
└──────────────────────────┘
```

## Best Practices

### Commands

```python
# ✅ Specific and clear
@dataclass(frozen=True, kw_only=True)
class CancelOrder(Command):
    order_id: str
    cancellation_reason: str
    refund_method: str

# ✅ Validation in the command
@dataclass(frozen=True, kw_only=True)
class UpdatePrice(Command):
    product_id: str
    new_price: float
    
    def __post_init__(self) -> None:
        if self.new_price < 0:
            raise ValueError("Price cannot be negative")

# ❌ Too generic
@dataclass(frozen=True, kw_only=True)
class OrderCommand(Command):
    action: str  # "create" | "cancel" | "update"
    data: dict   # Untyped!
```

### Events

```python
# ✅ Rich in information
@dataclass(frozen=True, kw_only=True)
class OrderShipped(Event):
    order_id: str
    tracking_number: str
    carrier: str
    estimated_delivery: str
    shipped_at: str

# ✅ Several small events instead of one big one
@dataclass(frozen=True, kw_only=True)
class OrderPlaced(Event):
    order_id: str
    ...

@dataclass(frozen=True, kw_only=True)
class PaymentReceived(Event):
    order_id: str
    payment_id: str
    ...

# ❌ Too little information
@dataclass(frozen=True, kw_only=True)
class OrderUpdated(Event):
    order_id: str
    # What was updated? When? By whom?
```

## Event Versioning

Events must remain **backward-compatible**:

```python
# Version 1
@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    email: str

# Version 2 - ✅ Backward compatible
@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    email: str
    username: str = ""  # Default for old events
    created_at: str = ""

# Version 2 - ❌ BREAKING CHANGE
@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    username: str  # email removed - breaks old events!
```

## Practical Example

```python
# Commands
@dataclass(frozen=True, kw_only=True)
class PlaceOrder(Command):
    order_id: str
    customer_id: str
    items: list[dict]

@dataclass(frozen=True, kw_only=True)
class PayOrder(Command):
    order_id: str
    payment_method: str
    amount: float

@dataclass(frozen=True, kw_only=True)
class ShipOrder(Command):
    order_id: str
    carrier: str

# Events
@dataclass(frozen=True, kw_only=True)
class OrderPlaced(Event):
    order_id: str
    customer_id: str
    total_amount: float

@dataclass(frozen=True, kw_only=True)
class OrderPaid(Event):
    order_id: str
    payment_id: str
    amount: float

@dataclass(frozen=True, kw_only=True)
class OrderShipped(Event):
    order_id: str
    tracking_number: str
    carrier: str

# Flow
bus.publish(PlaceOrder(...))  # → OrderPlaced
bus.publish(PayOrder(...))    # → OrderPaid
bus.publish(ShipOrder(...))   # → OrderShipped
```

## Next Steps

- [Message Bus](message-bus.md) - Routing & subscription
- [Event Store](event-store.md) - Persistence patterns
- [Best Practices](best-practices.md) - Production guidelines

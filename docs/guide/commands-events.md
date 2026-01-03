# Commands & Events

Commands und Events sind die beiden Haupt-Message-Typen in Orchestrix. Verstehe den Unterschied!

## Commands vs Events

| Aspekt | Command | Event |
|--------|---------|-------|
| **Bedeutung** | Intention (was soll passieren) | Fakt (was ist passiert) |
| **Zeitform** | Imperativ (CreateOrder) | Vergangenheit (OrderCreated) |
| **Handler** | Genau 1 Handler | 0 bis N Handler |
| **Validierung** | Kann rejected werden | Ist bereits passiert |
| **Quelle** | Application/User | Domain Logic |

## Commands

### Definition

Ein **Command** repräsentiert eine **Intention, State zu ändern**.

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

- **Imperativ**: CreateX, UpdateX, DeleteX, CancelX
- **Spezifisch**: Was genau soll passieren?
- **Domain Language**: Begriffe aus der Business-Domäne

```python
# ✅ Gut
class PlaceOrder(Command): pass
class CancelSubscription(Command): pass
class ApproveInvoice(Command): pass

# ❌ Schlecht
class OrderCommand(Command): pass  # Zu generisch
class DoSomething(Command): pass   # Nicht aussagekräftig
class Process(Command): pass       # Was wird processed?
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

Ein **Event** repräsentiert einen **Fakt, der bereits passiert ist**.

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

- **Vergangenheit**: XCreated, XUpdated, XDeleted, XCancelled
- **Fakt**: Was ist tatsächlich passiert?
- **Domain Events**: Business-relevante Ereignisse

```python
# ✅ Gut
class OrderPlaced(Event): pass
class SubscriptionCancelled(Event): pass
class InvoiceApproved(Event): pass
class PaymentReceived(Event): pass

# ❌ Schlecht
class OrderEvent(Event): pass     # Zu generisch
class OrderChange(Event): pass    # Was hat sich geändert?
class Updated(Event): pass        # Was wurde updated?
```

### Event Design

Events sollten **immutable** und **serializable** sein:

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
    
    # ❌ Keine mutable Objects!
    # settings: dict  # Besser: Eigenes dataclass
    
    # ✅ Immutable data
    # settings: UserSettings  # Eigenes frozen dataclass
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
# ✅ Spezifisch und klar
@dataclass(frozen=True, kw_only=True)
class CancelOrder(Command):
    order_id: str
    cancellation_reason: str
    refund_method: str

# ✅ Validation im Command
@dataclass(frozen=True, kw_only=True)
class UpdatePrice(Command):
    product_id: str
    new_price: float
    
    def __post_init__(self) -> None:
        if self.new_price < 0:
            raise ValueError("Price cannot be negative")

# ❌ Zu generisch
@dataclass(frozen=True, kw_only=True)
class OrderCommand(Command):
    action: str  # "create" | "cancel" | "update"
    data: dict   # Untyped!
```

### Events

```python
# ✅ Reich an Information
@dataclass(frozen=True, kw_only=True)
class OrderShipped(Event):
    order_id: str
    tracking_number: str
    carrier: str
    estimated_delivery: str
    shipped_at: str

# ✅ Mehrere kleine Events statt eines großen
@dataclass(frozen=True, kw_only=True)
class OrderPlaced(Event):
    order_id: str
    ...

@dataclass(frozen=True, kw_only=True)
class PaymentReceived(Event):
    order_id: str
    payment_id: str
    ...

# ❌ Zu wenig Information
@dataclass(frozen=True, kw_only=True)
class OrderUpdated(Event):
    order_id: str
    # Was wurde updated? Wann? Von wem?
```

## Event Versioning

Events müssen **backward-compatible** bleiben:

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
    username: str = ""  # Default für alte Events
    created_at: str = ""

# Version 2 - ❌ BREAKING CHANGE
@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    username: str  # email entfernt - bricht alte Events!
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

- [Message Bus](message-bus.md) - Routing & Subscription
- [Event Store](event-store.md) - Persistence Patterns
- [Best Practices](best-practices.md) - Production Guidelines

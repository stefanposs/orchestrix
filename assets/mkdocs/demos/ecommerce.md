
# E-Commerce Demo — Order Processing with Sagas

Multi-aggregate order processing with payment, inventory reservation,
automatic compensation on failure, and a full saga coordinator.

> **Source Code:**
> [`bases/orchestrix/ecommerce_demo/`](https://github.com/stefanposs/orchestrix/tree/main/bases/orchestrix/ecommerce_demo)

## Quick Start

```bash
uv run python -m bases.orchestrix.ecommerce_demo.main
```

## What It Demonstrates

- **Order state machine** — `PENDING` → `PAYMENT_PROCESSING` → `CONFIRMED` (or `CANCELLED`)
- **Multi-aggregate saga** — coordinates Order → Payment → Inventory
- **Compensation logic** — refund + release inventory on failure
- **Value objects** — `OrderItem`, `Address`, `PaymentDetails`
- **Command handlers** — `OrderCommandHandlers` processes all 7 commands

## Domain Model

### Commands

| Command | Key Fields | Description |
|---|---|---|
| `CreateOrder` | `order_id`, `customer_id`, `items`, `shipping_address` | Create a new order |
| `ProcessPayment` | `order_id`, `payment_id`, `amount`, `method` | Process payment |
| `ReserveInventory` | `order_id`, `items` | Reserve inventory |
| `ConfirmOrder` | `order_id` | Confirm the order |
| `CancelOrder` | `order_id`, `reason` | Cancel the order |
| `ReleaseInventory` | `order_id`, `reservation_id` | Compensation: release stock |
| `RefundPayment` | `order_id`, `payment_id`, `amount` | Compensation: refund |

### Events

| Event | Description |
|---|---|
| `OrderCreated` | Order created |
| `PaymentInitiated` | Payment processing started |
| `PaymentCompleted` | Payment succeeded |
| `PaymentFailed` | Payment rejected |
| `InventoryReserved` | Items reserved |
| `InventoryReservationFailed` | Not enough stock |
| `OrderConfirmed` | Order confirmed |
| `OrderCancelled` | Order cancelled |
| `OrderCompleted` | Order fulfilled |
| `InventoryReleased` | Reservation cancelled (compensation) |
| `PaymentRefunded` | Payment refunded (compensation) |

### Value Objects

```python
@dataclass(frozen=True)
class OrderItem:
    product_id: str
    quantity: int
    unit_price: Decimal

@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    postal_code: str
    country: str
```

### Aggregate: `Order`

State machine with status enum:

```python
class OrderStatus(str, Enum):
    PENDING = "pending"
    PAYMENT_PROCESSING = "payment_processing"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    INVENTORY_RESERVED = "inventory_reserved"
    INVENTORY_FAILED = "inventory_failed"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
```

## Saga Flow

```
CreateOrder
  ↓
OrderCreated → OrderSaga
  ↓
ProcessPayment
  ↓  success                      ↓  failure
PaymentCompleted → OrderSaga     PaymentFailed → CancelOrder ❌
  ↓
ReserveInventory
  ↓  success                      ↓  failure
InventoryReserved → OrderSaga    InventoryFailed → RefundPayment + CancelOrder ❌
  ↓
ConfirmOrder → OrderConfirmed ✅
```

## Code Structure

```
bases/orchestrix/ecommerce_demo/
├── main.py              # Runnable entry point (async demo)
├── models.py            # Commands, Events, Value Objects, Enums
├── aggregate.py         # Order aggregate with state machine
├── handlers.py          # OrderCommandHandlers
├── saga.py              # OrderSaga coordinator
├── validated_example.py # Validation-enhanced variant
└── README.md
```

## Related

- [Banking Demo](banking.md) — Saga pattern for money transfers
- [Notifications Demo](notifications.md) — Async event handlers
- [Lakehouse Demo](lakehouse.md) — Event sourcing with compliance

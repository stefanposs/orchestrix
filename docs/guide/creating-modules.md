# Creating Modules

Modules sind das Herzstück von Orchestrix. Sie kapseln Domain-Logik und registrieren Handler beim Message Bus.

## Was ist ein Module?

Ein **Module** ist eine Sammlung von:

- Commands und Events (Domain Messages)
- Aggregates (Domain Models)
- Command Handlers (Business Logic)
- Event Handlers (Projections, Side Effects)

## Basic Module Structure

```python
from orchestrix import Module, MessageBus, EventStore

class OrderModule(Module):
    """Order management domain module."""
    
    def register(self, bus: MessageBus, store: EventStore) -> None:
        """Register all handlers with infrastructure."""
        # Command handlers
        bus.subscribe(CreateOrder, CreateOrderHandler(bus, store))
        bus.subscribe(CancelOrder, CancelOrderHandler(bus, store))
        bus.subscribe(ShipOrder, ShipOrderHandler(bus, store))
        
        # Event handlers
        bus.subscribe(OrderCreated, self._send_confirmation_email)
        bus.subscribe(OrderShipped, self._update_inventory)
        bus.subscribe(OrderCancelled, self._process_refund)
    
    def _send_confirmation_email(self, event: OrderCreated) -> None:
        """Send order confirmation email."""
        print(f"📧 Sending confirmation email for order {event.order_id}")
    
    def _update_inventory(self, event: OrderShipped) -> None:
        """Update inventory after shipping."""
        print(f"📦 Updating inventory for order {event.order_id}")
    
    def _process_refund(self, event: OrderCancelled) -> None:
        """Process refund for cancelled order."""
        print(f"💰 Processing refund for order {event.order_id}")
```

## Module Organization

### 1. File Structure

Empfohlene Struktur für größere Projekte:

```
my_app/
├── domains/
│   ├── orders/
│   │   ├── __init__.py
│   │   ├── module.py          # OrderModule
│   │   ├── messages.py        # Commands & Events
│   │   ├── aggregates.py      # Order aggregate
│   │   └── handlers.py        # Command/Event handlers
│   ├── inventory/
│   │   ├── __init__.py
│   │   ├── module.py
│   │   ├── messages.py
│   │   └── ...
│   └── shipping/
│       └── ...
└── main.py                    # Application setup
```

### 2. Separate Messages

```python
# domains/orders/messages.py
from dataclasses import dataclass
from orchestrix import Command, Event

@dataclass(frozen=True, kw_only=True)
class CreateOrder(Command):
    order_id: str
    customer_id: str
    items: list[dict]

@dataclass(frozen=True, kw_only=True)
class OrderCreated(Event):
    order_id: str
    customer_id: str
    total_amount: float
```

### 3. Separate Handlers

```python
# domains/orders/handlers.py
from orchestrix import CommandHandler, MessageBus, EventStore

class CreateOrderHandler(CommandHandler[CreateOrder]):
    def __init__(self, bus: MessageBus, store: EventStore) -> None:
        self.bus = bus
        self.store = store
    
    def handle(self, command: CreateOrder) -> None:
        # Implementation
        pass
```

### 4. Module Definition

```python
# domains/orders/module.py
from orchestrix import Module, MessageBus, EventStore
from .messages import CreateOrder, OrderCreated
from .handlers import CreateOrderHandler

class OrderModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        bus.subscribe(CreateOrder, CreateOrderHandler(bus, store))
```

## Cross-Module Communication

Module kommunizieren nur über Events (nie direkt):

```python
# ✅ Gut: Event-basierte Kommunikation
class OrderModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        bus.subscribe(OrderCreated, CreateOrderHandler(bus, store))

class InventoryModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        # Reagiert auf OrderCreated Event
        bus.subscribe(OrderCreated, self._reserve_inventory)
    
    def _reserve_inventory(self, event: OrderCreated) -> None:
        # Reserve inventory when order is created
        pass

class ShippingModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        # Reagiert auch auf OrderCreated Event
        bus.subscribe(OrderCreated, self._calculate_shipping)
    
    def _calculate_shipping(self, event: OrderCreated) -> None:
        # Calculate shipping costs
        pass
```

## Module Testing

```python
import pytest
from orchestrix import InMemoryMessageBus, InMemoryEventStore

def test_order_module():
    # Arrange
    bus = InMemoryMessageBus()
    store = InMemoryEventStore()
    module = OrderModule()
    module.register(bus, store)
    
    # Act
    bus.publish(CreateOrder(
        order_id="ORD-001",
        customer_id="CUST-123",
        items=[{"sku": "ITEM-1", "qty": 2}]
    ))
    
    # Assert
    events = store.load("ORD-001")
    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)
```

## Best Practices

### ✅ DO

- **Kleine, fokussierte Module** - Ein Module = Eine Domain
- **Event-basierte Kommunikation** - Module wissen nichts voneinander
- **Klare Grenzen** - Jedes Module hat eigene Messages
- **Unabhängige Tests** - Module einzeln testbar

### ❌ DON'T

- **Keine direkten Abhängigkeiten** zwischen Modules
- **Keine geteilten Aggregates** zwischen Modules
- **Keine Commands zwischen Modules** - nur Events
- **Keine zirkulären Imports** zwischen Modules

## Module Lifecycle

```python
# 1. Create infrastructure
bus = InMemoryMessageBus()
store = InMemoryEventStore()

# 2. Register modules (Reihenfolge egal!)
OrderModule().register(bus, store)
InventoryModule().register(bus, store)
ShippingModule().register(bus, store)
PaymentModule().register(bus, store)

# 3. Start publishing commands
bus.publish(CreateOrder(...))
```

## Advanced: Module Dependencies

Wenn ein Module externe Services braucht:

```python
class NotificationModule(Module):
    def __init__(self, email_service: EmailService, sms_service: SmsService):
        self.email_service = email_service
        self.sms_service = sms_service
    
    def register(self, bus: MessageBus, store: EventStore) -> None:
        bus.subscribe(OrderCreated, self._send_notifications)
    
    def _send_notifications(self, event: OrderCreated) -> None:
        self.email_service.send(event.customer_email, "Order confirmed!")
        self.sms_service.send(event.customer_phone, "Order confirmed!")

# Setup
email_service = EmailService(config)
sms_service = SmsService(config)
NotificationModule(email_service, sms_service).register(bus, store)
```

## Next Steps

- [Commands & Events](commands-events.md) - Message Design Guidelines
- [Message Bus](message-bus.md) - Bus Patterns
- [Best Practices](best-practices.md) - Production Tips

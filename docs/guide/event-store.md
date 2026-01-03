# Event Store

Der Event Store speichert alle Events eines Aggregates - die "Source of Truth" für Event Sourcing.

## Was ist ein Event Store?

Ein **Event Store**:

- Speichert Events pro Aggregate
- Lädt Events in chronologischer Reihenfolge
- Ermöglicht Aggregate Reconstruction
- Ist **append-only** (keine Updates/Deletes!)

## Basic Usage

```python
from orchestrix import InMemoryEventStore

# Create store
store = InMemoryEventStore()

# Save events
events = [
    OrderCreated(order_id="ORD-001", ...),
    ItemAdded(order_id="ORD-001", ...),
    OrderPaid(order_id="ORD-001", ...)
]
store.save("ORD-001", events)

# Load events
all_events = store.load("ORD-001")
# → [OrderCreated, ItemAdded, OrderPaid]
```

## InMemoryEventStore

Die Standard-Implementierung für Development & Testing:

```python
from collections import defaultdict
from orchestrix import EventStore, Event

class InMemoryEventStore(EventStore):
    """In-memory event store using defaultdict."""
    
    def __init__(self) -> None:
        self._events: dict[str, list[Event]] = defaultdict(list)
    
    def save(self, aggregate_id: str, events: list[Event]) -> None:
        """Append events to aggregate stream."""
        self._events[aggregate_id].extend(events)
    
    def load(self, aggregate_id: str) -> list[Event]:
        """Load all events for aggregate."""
        return list(self._events[aggregate_id])
```

### Features

- ✅ **Append-only** - Events werden nur hinzugefügt
- ✅ **Chronologisch** - Events in Reihenfolge
- ✅ **Einfach** - Keine Dependencies
- ⚠️ **In-Memory** - Daten gehen bei Restart verloren

## Event Sourcing Pattern

### 1. Command → Events

Command Handler erstellt Aggregate und sammelt Events:

```python
class CreateOrderHandler(CommandHandler[CreateOrder]):
    def handle(self, command: CreateOrder) -> None:
        # Create aggregate
        order = Order.create(
            order_id=command.order_id,
            customer_id=command.customer_id,
            items=command.items
        )
        
        # Collect emitted events
        events = order.collect_events()
        # → [OrderCreated, ItemAdded, ItemAdded, ...]
        
        # Save to event store
        self.store.save(command.order_id, events)
        
        # Publish to bus
        for event in events:
            self.bus.publish(event)
```

### 2. Aggregate Reconstruction

Lade Aggregate aus Event Stream:

```python
class CancelOrderHandler(CommandHandler[CancelOrder]):
    def handle(self, command: CancelOrder) -> None:
        # Load all events for aggregate
        events = self.store.load(command.order_id)
        
        # Reconstruct aggregate from events
        order = self._reconstruct_order(events)
        
        # Execute business logic
        order.cancel()
        
        # Save new events
        new_events = order.collect_events()
        self.store.save(command.order_id, new_events)
        
        for event in new_events:
            self.bus.publish(event)
    
    def _reconstruct_order(self, events: list[Event]) -> Order:
        """Replay events to rebuild aggregate state."""
        order = None
        
        for event in events:
            if isinstance(event, OrderCreated):
                order = Order(
                    order_id=event.order_id,
                    customer_id=event.customer_id,
                    status="pending"
                )
            elif isinstance(event, ItemAdded):
                order.items.append(event.item)
            elif isinstance(event, OrderPaid):
                order.status = "paid"
            elif isinstance(event, OrderShipped):
                order.status = "shipped"
        
        return order
```

### 3. Complete Example

```python
from dataclasses import dataclass, field

@dataclass
class Order:
    """Order aggregate root."""
    order_id: str
    customer_id: str
    items: list = field(default_factory=list)
    status: str = "draft"
    _events: list[Event] = field(default_factory=list, repr=False)
    
    @classmethod
    def create(cls, order_id: str, customer_id: str, items: list):
        """Create new order."""
        order = cls(order_id=order_id, customer_id=customer_id)
        order._events.append(OrderCreated(
            order_id=order_id,
            customer_id=customer_id
        ))
        for item in items:
            order.add_item(item)
        return order
    
    def add_item(self, item: dict) -> None:
        """Add item to order."""
        self.items.append(item)
        self._events.append(ItemAdded(
            order_id=self.order_id,
            item=item
        ))
    
    def cancel(self) -> None:
        """Cancel order."""
        if self.status == "shipped":
            raise ValueError("Cannot cancel shipped order")
        self.status = "cancelled"
        self._events.append(OrderCancelled(
            order_id=self.order_id
        ))
    
    def collect_events(self) -> list[Event]:
        """Get and clear pending events."""
        events = self._events.copy()
        self._events.clear()
        return events
    
    @classmethod
    def from_events(cls, events: list[Event]) -> "Order":
        """Reconstruct from event stream."""
        order = None
        for event in events:
            if isinstance(event, OrderCreated):
                order = cls(
                    order_id=event.order_id,
                    customer_id=event.customer_id
                )
            elif isinstance(event, ItemAdded):
                order.items.append(event.item)
            elif isinstance(event, OrderCancelled):
                order.status = "cancelled"
        return order
```

## Event Store Benefits

### 1. Complete Audit Trail

```python
# Jedes Event ist dokumentiert
events = store.load("ORD-001")
for event in events:
    print(f"{event.timestamp}: {event.type}")

# Output:
# 2026-01-03T10:00:00: OrderCreated
# 2026-01-03T10:01:00: ItemAdded
# 2026-01-03T10:02:00: ItemAdded
# 2026-01-03T10:05:00: OrderPaid
# 2026-01-03T10:30:00: OrderShipped
```

### 2. Time Travel

```python
def get_order_at_time(order_id: str, timestamp: str) -> Order:
    """Get order state at specific point in time."""
    events = store.load(order_id)
    
    # Filter events up to timestamp
    past_events = [
        e for e in events
        if e.timestamp <= timestamp
    ]
    
    return Order.from_events(past_events)

# Was the state at 10:03?
order = get_order_at_time("ORD-001", "2026-01-03T10:03:00")
print(order.status)  # → "pending" (before payment)
```

### 3. Event Replay

```python
def replay_all_events(store: EventStore, bus: MessageBus):
    """Replay all events (rebuild projections)."""
    for aggregate_id in store.get_all_aggregate_ids():
        events = store.load(aggregate_id)
        for event in events:
            bus.publish(event)
```

### 4. Debugging

```python
# Debug: What happened to this order?
events = store.load("ORD-123")
for i, event in enumerate(events, 1):
    print(f"{i}. {event.__class__.__name__}")
    print(f"   Time: {event.timestamp}")
    print(f"   Data: {event}")
```

## Persistence Strategies

### Strategy 1: JSON File Store

```python
import json
from pathlib import Path

class FileEventStore(EventStore):
    """Event store using JSON files."""
    
    def __init__(self, base_path: str = "./events"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def save(self, aggregate_id: str, events: list[Event]) -> None:
        file_path = self.base_path / f"{aggregate_id}.jsonl"
        
        with file_path.open("a") as f:
            for event in events:
                json_event = {
                    "type": event.__class__.__name__,
                    "data": asdict(event)
                }
                f.write(json.dumps(json_event) + "\n")
    
    def load(self, aggregate_id: str) -> list[Event]:
        file_path = self.base_path / f"{aggregate_id}.jsonl"
        
        if not file_path.exists():
            return []
        
        events = []
        with file_path.open("r") as f:
            for line in f:
                json_event = json.loads(line)
                # Deserialize event
                event_class = globals()[json_event["type"]]
                events.append(event_class(**json_event["data"]))
        
        return events
```

### Strategy 2: SQLite Store

```python
import sqlite3
import json

class SQLiteEventStore(EventStore):
    """Event store using SQLite."""
    
    def __init__(self, db_path: str = "events.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()
    
    def _create_table(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aggregate_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()
    
    def save(self, aggregate_id: str, events: list[Event]) -> None:
        for event in events:
            self.conn.execute("""
                INSERT INTO events (aggregate_id, event_type, event_data, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                aggregate_id,
                event.__class__.__name__,
                json.dumps(asdict(event)),
                event.timestamp
            ))
        self.conn.commit()
    
    def load(self, aggregate_id: str) -> list[Event]:
        cursor = self.conn.execute("""
            SELECT event_type, event_data
            FROM events
            WHERE aggregate_id = ?
            ORDER BY id ASC
        """, (aggregate_id,))
        
        events = []
        for event_type, event_data in cursor:
            event_class = globals()[event_type]
            events.append(event_class(**json.loads(event_data)))
        
        return events
```

### Strategy 3: PostgreSQL Store (Production)

```python
import psycopg2
from psycopg2.extras import Json

class PostgreSQLEventStore(EventStore):
    """Production-grade PostgreSQL event store."""
    
    def __init__(self, connection_string: str):
        self.conn = psycopg2.connect(connection_string)
        self._create_table()
    
    def _create_table(self):
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id BIGSERIAL PRIMARY KEY,
                    aggregate_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data JSONB NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(aggregate_id, version)
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_aggregate_id
                ON events(aggregate_id)
            """)
        self.conn.commit()
```

## Best Practices

### ✅ DO

- **Append-Only** - Niemals Events löschen oder ändern
- **Immutable Events** - Events sind unveränderlich
- **Versionierung** - Track Event Version für Optimistic Locking
- **Snapshots** - Für lange Event Streams (>1000 Events)

### ❌ DON'T

- **Keine Updates** - Events werden nie geändert
- **Keine Deletes** - Events werden nie gelöscht
- **Keine Sensitive Data** - PII gehört nicht in Events
- **Keine großen Payloads** - Referenzen statt große Objekte

## Next Steps

- [Best Practices](best-practices.md) - Production Guidelines
- [Testing](../development/testing.md) - Test Strategies
- [Architecture](../development/architecture.md) - System Design

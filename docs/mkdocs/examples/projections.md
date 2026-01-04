# Projections - Building Read Models

Projections transform event streams into optimized read models for queries.

## Overview

Projections listen to events and build denormalized views optimized for specific queries. This separates write models (aggregates) from read models (projections).

## Key Features

- **Multiple Backends** - InMemory, PostgreSQL, custom
- **Automatic Updates** - React to events automatically
- **Query Optimization** - Denormalized for fast reads
- **Rebuild Support** - Replay events to rebuild projections

## Basic Example

```python
from orchestrix.core.projection import Projection, ProjectionEngine
from orchestrix.infrastructure import InMemoryMessageBus
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderCreated(Event):
    order_id: str
    customer_name: str
    total_amount: float

@dataclass(frozen=True)
class OrderShipped(Event):
    order_id: str
    tracking_number: str

class OrderSummaryProjection(Projection):
    """Read model for order summaries."""
    
    def __init__(self):
        self.orders = {}
    
    async def project(self, event: Event):
        if isinstance(event, OrderCreated):
            self.orders[event.order_id] = {
                'customer': event.customer_name,
                'total': event.total_amount,
                'status': 'created'
            }
        elif isinstance(event, OrderShipped):
            if event.order_id in self.orders:
                self.orders[event.order_id]['status'] = 'shipped'
                self.orders[event.order_id]['tracking'] = event.tracking_number
    
    def get_order(self, order_id: str):
        return self.orders.get(order_id)
    
    def get_all_orders(self):
        return list(self.orders.values())

# Setup
bus = InMemoryMessageBus()
engine = ProjectionEngine()
projection = OrderSummaryProjection()

# Register
engine.register_projection(projection, [OrderCreated, OrderShipped])
engine.start(bus)

# Query
summary = projection.get_order("ORD-001")
all_orders = projection.get_all_orders()
```

## PostgreSQL Backend

```python
from orchestrix.core.projection import PostgreSQLProjectionStore

class OrderProjection(Projection):
    def __init__(self, store: PostgreSQLProjectionStore):
        self.store = store
    
    async def project(self, event: Event):
        if isinstance(event, OrderCreated):
            await self.store.execute(
                """
                INSERT INTO order_summary (order_id, customer, total, status)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (order_id) DO UPDATE
                SET customer = $2, total = $3, status = $4
                """,
                event.order_id,
                event.customer_name,
                event.total_amount,
                'created'
            )
```

## Running the Example

```bash
cd examples/projections
uv run example.py
```

## Use Cases

- **Dashboard Views** - Real-time business metrics
- **Search Indexes** - Optimized for full-text search
- **Reporting** - Analytics and reports
- **Customer Views** - Personalized customer portals

## Best Practices

1. **Idempotency** - Handle duplicate events gracefully
2. **Versioning** - Support projection schema evolution
3. **Rebuild Strategy** - Plan for rebuilding projections
4. **Performance** - Index frequently queried fields

## Learn More

- [Projection Guide](../guide/projections.md)
- [Full Example](https://github.com/stefanposs/orchestrix/tree/main/examples/projections)
- [API Reference](../api/core.md#projection)

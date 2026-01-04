# Event Versioning

Event versioning allows you to evolve event schemas over time while maintaining backward compatibility.

## Overview

As your application evolves, event structures change. Event versioning with upcasters allows old events to be automatically transformed to new schemas when loaded.

## Key Features

- **Upcasters** - Transform old events to new versions
- **Version Detection** - Automatic version detection
- **Multiple Versions** - Support multiple schema versions
- **Backward Compatible** - Old events work with new code

## Basic Example

### Version 1 (Initial)

```python
from dataclasses import dataclass
from orchestrix.core.message import Event

@dataclass(frozen=True, kw_only=True)
class OrderCreatedV1(Event):
    """Initial version - single address field."""
    order_id: str
    customer_name: str
    address: str  # Single address field
    total_amount: float
```

### Version 2 (Split Address)

```python
@dataclass(frozen=True, kw_only=True)
class OrderCreatedV2(Event):
    """Version 2 - structured address."""
    order_id: str
    customer_name: str
    street: str
    city: str
    country: str
    total_amount: float
```

### Upcaster

```python
from orchestrix.core.versioning import Upcaster, VersionRegistry

class OrderCreatedV1ToV2(Upcaster):
    """Upcasts V1 events to V2 format."""
    
    def can_upcast(self, event: Event) -> bool:
        return isinstance(event, OrderCreatedV1)
    
    def upcast(self, event: OrderCreatedV1) -> OrderCreatedV2:
        # Parse single address into components
        parts = event.address.split(", ")
        return OrderCreatedV2(
            order_id=event.order_id,
            customer_name=event.customer_name,
            street=parts[0] if len(parts) > 0 else "",
            city=parts[1] if len(parts) > 1 else "",
            country=parts[2] if len(parts) > 2 else "",
            total_amount=event.total_amount
        )

# Register upcaster
registry = VersionRegistry()
registry.register_upcaster(OrderCreatedV1ToV2())

# Load events - old events automatically upcasted
events = store.load("order-123")
for event in events:
    # V1 events are automatically converted to V2
    if isinstance(event, OrderCreatedV2):
        print(f"Order in {event.city}, {event.country}")
```

## Chained Upcasters

Support multiple version transitions:

```python
# V1 -> V2 -> V3
class OrderCreatedV2ToV3(Upcaster):
    """Adds email field."""
    
    def upcast(self, event: OrderCreatedV2) -> OrderCreatedV3:
        return OrderCreatedV3(
            order_id=event.order_id,
            customer_name=event.customer_name,
            street=event.street,
            city=event.city,
            country=event.country,
            email="",  # Default value for new field
            total_amount=event.total_amount
        )

# Register both
registry.register_upcaster(OrderCreatedV1ToV2())
registry.register_upcaster(OrderCreatedV2ToV3())

# V1 events automatically go through both upcasters
```

## Version Metadata

Add version information to events:

```python
@dataclass(frozen=True, kw_only=True)
class OrderCreatedV2(Event):
    order_id: str
    customer_name: str
    street: str
    city: str
    country: str
    total_amount: float
    
    def __post_init__(self):
        super().__post_init__()
        # Add version to metadata
        object.__setattr__(self, 'version', 2)
```

## Running the Example

```bash
cd examples/versioning
uv run example.py
```

## Use Cases

- **Schema Evolution** - Add/remove/rename fields
- **Data Migration** - Transform old data formats
- **Backward Compatibility** - Support multiple client versions
- **Technical Debt** - Gradually migrate to new schemas

## Best Practices

1. **Immutable Events** - Never change existing event classes
2. **Version Numbers** - Use explicit version numbers (V1, V2, V3)
3. **Default Values** - Provide sensible defaults for new fields
4. **Testing** - Test all upcaster chains thoroughly
5. **Documentation** - Document version changes in CHANGELOG

## Strategies

### Copy-and-Transform

Create new event class, transform in upcaster:

```python
# Good: Clear version separation
class OrderCreatedV1(Event): ...
class OrderCreatedV2(Event): ...
class V1ToV2Upcaster(Upcaster): ...
```

### In-Place Migration

One-time migration script:

```python
# For breaking changes
async def migrate_events():
    for aggregate_id in all_aggregates:
        events = store.load(aggregate_id)
        new_events = [upcast(e) for e in events]
        # Save to new store or overwrite
```

### Weak Schema

Use dict-based events (not recommended):

```python
# Avoid: Loses type safety
event = {"type": "OrderCreated", "data": {...}}
```

## Version Detection

Detect event version automatically:

```python
def get_version(event: Event) -> int:
    if hasattr(event, 'version'):
        return event.version
    
    # Fallback: detect by class name
    if 'V1' in event.__class__.__name__:
        return 1
    elif 'V2' in event.__class__.__name__:
        return 2
    
    return 1  # Default to V1
```

## Learn More

- [Best Practices](../guide/best-practices.md)
- [Full Example](https://github.com/stefanposs/orchestrix/tree/main/examples/versioning)
- [API Reference](../api/core.md#versioning)

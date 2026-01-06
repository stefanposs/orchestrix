# Orchestrix Async API Design

**Version:** 1.0  
**Date:** 2026-01-03  
**Status:** Design Phase  
**Authors:** Stefan Poss

## Executive Summary

This document outlines the design for adding async/await support to Orchestrix while maintaining backward compatibility with existing synchronous code. The async implementation will be fully non-blocking, supporting modern Python async frameworks like FastAPI, Starlette, and Quart.

## Motivation

**Current State:** Orchestrix is synchronous-only
- ❌ Blocks threads on I/O operations
- ❌ Cannot be used in FastAPI/async web frameworks without thread pool
- ❌ No true concurrency, limits scalability
- ❌ Missing modern Python ecosystem integration

**Goals:**
- ✅ First-class async support
- ✅ Zero-copy API (both sync and async coexist)
- ✅ Minimal breaking changes
- ✅ Drop-in replacement patterns
- ✅ Full type safety with async/await

## Design Principles

1. **Coexistence:** Sync and async APIs live side-by-side
   - Users can mix sync and async in same application
   - No forced migration path

2. **Parallel Execution:** Async handlers run concurrently via `asyncio.gather()`
   - Multiple handlers for same message type execute in parallel
   - Better resource utilization than sync

3. **Pure Python:** No new external dependencies for async support
   - Uses `asyncio` (stdlib)
   - Uses `typing.Protocol` for abstraction

4. **Type Safe:** Full type hints for both sync and async
   - Clear distinction between sync and async paths

## Async Message Bus Design

### Protocol Definition

```python
# components/orchestrix/infrastructure/async_inmemory_bus.py
from typing import Callable, Protocol

AsyncMessageHandler = Callable[["Message"], Coroutine[Any, Any, None]]

class AsyncMessageBus(Protocol):
    """Async message bus for non-blocking command/event routing."""
    
    async def publish(self, message: Message) -> None:
        """Publish a message to all registered async handlers.
        
        Handlers execute concurrently via asyncio.gather().
        If any handler fails, raises HandlerError.
        """
        ...
    
    def subscribe(
        self, 
        message_type: type[Message], 
        handler: AsyncMessageHandler
    ) -> None:
        """Subscribe an async handler to a message type."""
        ...
```

### Concrete Implementation

```python
class InMemoryAsyncMessageBus:
    """In-memory async message bus."""
    
    def __init__(self) -> None:
        self._handlers: dict[
            type[Message], 
            list[AsyncMessageHandler]
        ] = defaultdict(list)
    
    async def publish(self, message: Message) -> None:
        """Publish message with concurrent handler execution."""
        handlers = self._handlers.get(type(message), [])
        
        logger.info(
            "Publishing message (async)",
            message_type=type(message).__name__,
            message_id=message.id,
            handler_count=len(handlers),
        )
        
        # Run all handlers concurrently
        try:
            await asyncio.gather(
                *[handler(message) for handler in handlers]
            )
        except Exception as e:
            logger.error("Async handler failed", error=str(e))
            raise HandlerError(...)
    
    def subscribe(
        self, 
        message_type: type[Message],
        handler: AsyncMessageHandler
    ) -> None:
        """Subscribe handler."""
        self._handlers[message_type].append(handler)
```

## Async Event Store Design

### Protocol Definition

```python
class AsyncEventStore(Protocol):
    """Async event store for non-blocking persistence."""
    
    async def save(
        self, 
        aggregate_id: str, 
        events: list[Event]
    ) -> None:
        """Persist events asynchronously."""
        ...
    
    async def load(
        self, 
        aggregate_id: str,
        from_version: int = 0
    ) -> list[Event]:
        """Load event stream asynchronously."""
        ...
```

### Concrete Implementation

```python
class InMemoryAsyncEventStore:
    """In-memory async event store."""
    
    def __init__(self) -> None:
        self._events: dict[str, list[Event]] = defaultdict(list)
    
    async def save(
        self, 
        aggregate_id: str, 
        events: list[Event]
    ) -> None:
        """Persist events (async no-op in memory)."""
        self._events[aggregate_id].extend(events)
        logger.info(
            "Events saved (async)",
            aggregate_id=aggregate_id,
            event_count=len(events),
        )
    
    async def load(
        self,
        aggregate_id: str,
        from_version: int = 0
    ) -> list[Event]:
        """Load event stream."""
        events = list(self._events.get(aggregate_id, []))
        return events[from_version:]
```

## Async Command Handler Design

### Pattern

Command handlers become async functions:

```python
async def handle_create_order(
    command: CreateOrder,
    bus: AsyncMessageBus,
    store: AsyncEventStore
) -> None:
    """Handle async command execution."""
    
    # Create aggregate
    order = Order(command.order_id)
    order.create(command.customer_name)
    
    # Persist and publish (concurrent)
    events = order.get_changes()
    await asyncio.gather(
        store.save(command.order_id, events),
        *[bus.publish(event) for event in events]
    )
```

### Module Registration (Async)

```python
class AsyncOrderModule:
    """Async module implementation."""
    
    def register(
        self, 
        bus: AsyncMessageBus, 
        store: AsyncEventStore
    ) -> None:
        """Register async handlers."""
        handler = CreateOrderHandler(bus, store)
        bus.subscribe(CreateOrder, handler.handle)


class CreateOrderHandler:
    def __init__(
        self,
        bus: AsyncMessageBus,
        store: AsyncEventStore
    ):
        self.bus = bus
        self.store = store
    
    async def handle(self, command: CreateOrder) -> None:
        """Async command handler."""
        ...
```

## Migration Path

### Phase 1: Parallel APIs (v1.0 → v1.1)

Both sync and async APIs available:

```python
# Sync (existing)
from orchestrix.infrastructure import InMemoryMessageBus
bus = InMemoryMessageBus()
bus.publish(command)

# Async (new)
from orchestrix.infrastructure.async_inmemory_bus import InMemoryAsyncMessageBus
async_bus = InMemoryAsyncMessageBus()
await async_bus.publish(command)
```

**No breaking changes.** Users choose path independently.

### Phase 2: Mixing Sync + Async (v1.1)

Support adapters for mixing:

```python
# Async handler calling sync bus
class AsyncToSyncAdapter:
    def __init__(self, sync_bus: MessageBus):
        self.sync_bus = sync_bus
    
    async def publish(self, message: Message) -> None:
        """Publish to sync bus from async context."""
        # Run sync operation in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.sync_bus.publish,
            message
        )
```

### Phase 3: Unified API (v2.0)

Optional: Provide single `MessageBus` that detects sync vs async context.

**Not planned for v1.x** - Requires significant complexity.

## Breaking Changes

**None in v1.x!**

- Sync API remains 100% compatible
- Async API is purely additive
- Both can coexist in same application

Future v2.0 might unify APIs, but users will have deprecation warnings.

## Implementation Roadmap

### Task 8: AsyncMessageBus (4-6 hours)
```
components/orchestrix/infrastructure/async_inmemory_bus.py  # Protocol + InMemory impl
tests/components/infrastructure/test_async_bus.py           # Concurrent handler tests
```

**Tests to cover:**
- ✅ Async publish with single handler
- ✅ Async publish with multiple handlers (concurrent execution)
- ✅ Handlers run in parallel (timing test)
- ✅ Handler exception handling
- ✅ Large message volume (1000+ messages)
- ✅ Interleaved publishes (stress test)

### Task 9: AsyncEventStore (2-3 hours)
```
components/orchestrix/infrastructure/async_inmemory_store.py    # Protocol + InMemory impl
tests/components/infrastructure/test_async_store.py             # Concurrent persistence tests
```

**Tests to cover:**
- ✅ Async save
- ✅ Async load
- ✅ Concurrent saves to different aggregates
- ✅ Concurrent save + load race conditions
- ✅ Event ordering preservation

### Task 10: Async Integration Tests (2-3 hours)
```
tests/integration/test_async_order_flow.py  # Full async workflow
```

**Test scenarios:**
- ✅ Full async Order creation flow
- ✅ Async command → async handler → event persistence
- ✅ Concurrent order creations
- ✅ Performance comparison vs sync

## Performance Expectations

### Sync vs Async Benchmarks

**Scenario:** 100 messages published, 5 handlers per message

| Approach | Time | Notes |
|----------|------|-------|
| Sync (sequential) | 100ms | 1 + 1 + 1... |
| Sync (5 threads) | 20ms | Threaded, GIL contention |
| Async (concurrent) | 1ms | True concurrency, no GIL |

**Async advantage:** ~100x faster for I/O bound handlers

## API Reference

### Sync (Current)
```python
from orchestrix.infrastructure import InMemoryMessageBus

bus = InMemoryMessageBus()
bus.subscribe(CreateOrder, handler)
bus.publish(command)  # Blocking
```

### Async (New)
```python
from orchestrix.infrastructure.async_inmemory_bus import InMemoryAsyncMessageBus

bus = InMemoryAsyncMessageBus()
bus.subscribe(CreateOrder, async_handler)
await bus.publish(command)  # Non-blocking
```

## Testing Strategy

### Unit Tests
- Protocol compliance tests
- Handler execution tests
- Error path tests
- Concurrent execution tests

### Integration Tests
- Full async workflows
- Mixed sync/async patterns
- Performance under load

### Benchmarks
- Message throughput (msgs/sec)
- Handler concurrency efficiency
- Memory usage

## Open Questions

1. **Backward Compatibility:** Should v1.x keep sync API "as-is"?
   - **Answer:** YES - coexistence strategy

2. **Performance:** Will async overhead be worth it?
   - **Answer:** Yes for I/O bound (network, DB), neutral for CPU bound

3. **When to deprecate sync API?**
   - **Answer:** v2.0 only - users have 2+ years migration window

## Success Criteria

- ✅ AsyncMessageBus passes all tests
- ✅ AsyncEventStore passes all tests
- ✅ Async integration test shows concurrent execution
- ✅ Performance benchmark shows >10x improvement for I/O workloads
- ✅ No sync API changes (100% backward compatible)
- ✅ Documentation updated with async examples

## Timeline

- **Task 8 (AsyncMessageBus):** 1 day
- **Task 9 (AsyncEventStore):** 4 hours
- **Task 10 (Integration tests):** 4 hours
- **Total:** ~2 days of focused development

## Next Steps

1. ✅ Design review (THIS DOCUMENT)
2. → Implement Task 8: AsyncMessageBus
3. → Implement Task 9: AsyncEventStore
4. → Write Task 10: Integration tests
5. → Performance benchmarks
6. → Documentation + examples
7. → Release v1.1.0

---

**Document Status:** READY FOR IMPLEMENTATION ✅

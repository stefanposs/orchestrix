# Async/Sync Consolidation Decision

## Problem Statement

The codebase has duplicate implementations for two core infrastructure components:
- `inmemory_bus.py` (102 lines) + `async_inmemory_bus.py` (100 lines)  
- `inmemory_store.py` (88 lines) + `async_inmemory_store.py` (91 lines)

Total duplication: ~380 lines

## Analysis

### MessageBus Duplication (Cannot Be Consolidated)

**Reason:** Different execution semantics

**Sync Implementation:**
```python
for handler in handlers:
    handler(message)  # Sequential execution
```

**Async Implementation:**
```python
tasks = [handler(message) for handler in handlers]
await asyncio.gather(*tasks)  # Concurrent execution
```

These are fundamentally different behaviors:
- **Sequential**: Handlers execute one-at-a-time, in registration order
- **Concurrent**: Handlers execute in parallel via asyncio.gather()

Consolidating would require:
1. **asyncio.run() wrapper**: Causes nested event loop errors (tested, fails)
2. **Single async class**: Breaks sync interface, requires refactoring all sync tests
3. **Method overloading**: Not possible in Python (can't have sync and async versions with same name)

**Decision:** ACCEPT DUPLICATION - Different execution models require separate implementations

---

### EventStore Duplication (Could Be Consolidated - Deferred)

**Reason:** Logic is identical, only async/await keywords differ

**Sync & Async Implementations:**
```python
def save(self, aggregate_id, events):      # Sync version
    self._events[aggregate_id].extend(events)

async def save(self, aggregate_id, events):  # Async version  
    self._events[aggregate_id].extend(events)
```

The duplication is purely syntactic: only the `async` keyword and potential `await` statements differ.

**Consolidation Options:**

1. **Single Class with Both Methods** (Best):
   - `save()` - sync
   - `async_save()` - async wrapper that calls sync
   - Problem: Tests expect `await store.save()` (no prefix)
   - Would require updating all async tests to use `async_save()`

2. **Re-export Pattern** (Current):
   - Keep separate implementations
   - `async_inmemory_store.py` imports and aliases `InMemoryEventStore`
   - Maintainable but still has code duplication

3. **Protocol-Based Approach** (Future):
   - Create shared base logic
   - Both inherit and implement interface
   - Requires significant refactoring

**Decision:** DEFER - Accept current duplication (~180 lines total)
- Event store duplication is lower priority than message bus
- Consolidation would require breaking async test interface
- Can be addressed in future refactoring iteration

---

## Recommendations for Future

### Short Term (Next Sprint)
- Document both implementations with clear comments explaining duplication
- Add metrics to track this technical debt

### Medium Term (2-3 Sprints)
- Refactor event store tests to use `async_save()` pattern
- Consolidate to single unified implementation
- Reduces ~180 lines of duplication

### Long Term (Architectural)
- Consider message bus consolidation with adapter pattern
- Evaluate protocol/ABC approach for better type checking
- May be worth revisiting with Python 3.12+ features

---

## Status

- ✅ Phase 1: Core.Event fix + mock elimination (Complete)
- ✅ Phase 2: Snapshot tests (Complete)
- ✅ Phase 3: Async/sync consolidation analysis (Complete)
  - Message Bus: Duplication accepted (different semantics)
  - Event Store: Duplication deferred (low priority refactoring)
- ⏳ Phase 4: Final verification (Next)

## Tests
- All tests pass: 146 passed, 2 skipped
- No test failures or regressions
- Full coverage maintained

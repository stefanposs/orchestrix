# Saga Pattern Example

This example demonstrates the **Saga Pattern** for handling **distributed transactions** across multiple aggregates without traditional ACID guarantees.

## Overview

A **saga** is a long-running transaction that spans multiple services/aggregates and uses **compensation** (rollback) instead of traditional database transactions.

### When to Use Sagas

- **Distributed systems**: Transactions spanning multiple services/databases
- **Eventual consistency**: Accept temporary inconsistency with rollback capability
- **No distributed locks**: Avoid performance impact of database locks
- **Independent services**: Each service manages its own data

### When NOT to Use Sagas

- **Local transactions**: Use database transactions within a single service
- **Strong consistency required**: Need immediate consistency guarantees
- **High volume**: Saga overhead too high (overhead per transaction)
- **Complex rollback**: Compensation logic becomes too complex

## Architecture

### Choreography vs Orchestration

**Choreography** (Event-Driven):
```
EventA → Service 1 emits Event B
       → Service 2 listens, does work, emits Event C
       → Service 3 listens, does work, emits Event D
```
- Pros: Loose coupling, distributed
- Cons: Hard to trace, complex error handling

**Orchestration** (This Implementation):
```
Saga Orchestrator
  ├─→ Step 1: Action A
  ├─→ Step 2: Action B
  ├─→ Step 3: Action C
  └─→ Compensate in reverse on failure
```
- Pros: Clear flow, centralized error handling
- Cons: Single point of failure (but can be recovered)

## Money Transfer Example

### Flow Diagram

**Happy Path (Success)**:
```
Start
  ↓
Debit Source Account (-150)
  ↓
Credit Destination Account (+150)
  ↓
Complete ✓
```

**Failure Path (Insufficient Funds)**:
```
Start
  ↓
Debit Source Account (-150)
  ↓
Credit Destination Account (+150)
  ↓
ERROR: Account not found!
  ↓
Compensate: Credit Source (+150)  [Reverse debit]
  ↓
Failed ✗
```

### Key Features

1. **Compensation-Based Rollback**
   - Each step has an action and optional compensation
   - On failure, execute compensations in reverse order
   - Restores system to consistent state

2. **State Tracking**
   - Track which steps have been completed
   - Persist state for recovery from crashes
   - Monitor saga health and failures

3. **Idempotent Design**
   - Safe to retry steps
   - Safe to replay sagas
   - Handles duplicate messages

4. **Error Handling**
   - Clear error propagation
   - Automatic compensation
   - Recovery from failures

## Running the Example

```bash
python -m examples.sagas.example
```

### Expected Output

```
============================================================
SAGA PATTERN EXAMPLE: Money Transfer
============================================================

📊 Account Balances:
  Alice        (ACC-001):  1000.00
  Bob          (ACC-002):   500.00
  Charlie      (ACC-003):   750.00

============================================================
TEST 1: Successful Money Transfer
============================================================

Executing transfer from Alice to Bob (150)...
✓ Debited $150 from Alice (ACC-001)
  New balance: $850.0
✓ Credited $150 to Bob (ACC-002)
  New balance: $650.0

✅ Transfer successful!
Saga Status: completed

📊 Account Balances:
  Alice        (ACC-001):   850.00
  Bob          (ACC-002):   650.00
  Charlie      (ACC-003):   750.00

============================================================
TEST 2: Transfer with Insufficient Funds
============================================================

Attempting transfer from Bob to Charlie (1000)...

❌ Transfer failed: Insufficient funds: 650.0 < 1000.0
Saga Status: failed

✓ Compensations executed (balances restored)

📊 Account Balances:
  Alice        (ACC-001):   850.00
  Bob          (ACC-002):   650.00
  Charlie      (ACC-003):   750.00
```

## Saga Implementation

### Creating a Saga

```python
from orchestrix.core import Saga, SagaStep, InMemorySagaStateStore

# Define steps with actions and compensations
steps = [
    SagaStep(
        name="step1",
        action=debit_account,      # What to do
        compensation=credit_back    # How to undo
    ),
    SagaStep(
        name="step2",
        action=credit_account,
        compensation=debit_back
    )
]

# Create saga
state_store = InMemorySagaStateStore()
saga = Saga("TransferMoney", steps, state_store)
await saga.initialize()

# Execute
try:
    result = await saga.execute(from_account=..., to_account=..., amount=...)
except Exception as e:
    # Compensations already executed
    print(f"Saga failed: {e}")
```

### Action and Compensation Functions

```python
async def debit_account(from_account: str, amount: float, **kwargs) -> dict:
    """Action: debit account, return details."""
    # Perform debit
    return {"account_id": from_account, "amount": amount}

async def credit_account(to_account: str, amount: float, **kwargs) -> dict:
    """Action: credit account, return details."""
    # Perform credit
    return {"account_id": to_account, "amount": amount}

async def compensate_debit(result: dict, **kwargs):
    """Compensation: undo the debit."""
    # Result contains what was debited
    # Perform credit to restore balance
    pass

async def compensate_credit(result: dict, **kwargs):
    """Compensation: undo the credit."""
    # Result contains what was credited
    # Perform debit to restore balance
    pass
```

### Saga State

```python
# Check saga status
state = saga.get_state()
print(f"Status: {state.status}")              # pending, in_progress, completed, failed
print(f"Completed: {saga.is_completed()}")    # True if done
print(f"Successful: {saga.is_successful()}")  # True if no errors

# Step-level details
for step_name, step_status in state.step_statuses.items():
    print(f"{step_name}: {step_status.status}")
    if step_status.result:
        print(f"  Result: {step_status.result}")
    if step_status.error:
        print(f"  Error: {step_status.error}")
```

## Key Concepts

### Idempotency

Each step must be idempotent - safe to execute multiple times:

```python
async def debit_account(account_id: str, amount: float, **kwargs):
    # Good: Check if already debited
    if account.already_debited:
        return stored_result
    
    # Bad: Always debit (not idempotent)
    account.balance -= amount
```

### Compensation Idempotency

Compensations must also be idempotent:

```python
async def compensate_debit(result: dict, **kwargs):
    # Good: Check if already compensated
    if account.already_compensated:
        return
    
    # Perform compensation
    account.balance += result["amount"]
    account.already_compensated = True
```

### Eventual Consistency

During saga execution, data may be temporarily inconsistent:

```
Time 0: Account A = $1000, Account B = $500
Time 1: Debit A → Account A = $850, Account B = $500  [Inconsistent!]
Time 2: Credit B → Account A = $850, Account B = $650  [Consistent]
```

This is acceptable in distributed systems with compensation-based recovery.

## Best Practices

1. **Keep steps small** - Simpler compensations
2. **Make everything idempotent** - Safe to retry
3. **Add timeouts** - Handle hanging steps
4. **Monitor sagas** - Track failures and performance
5. **Test compensations** - Ensure rollback works
6. **Document data consistency** - Explain intermediate states
7. **Use unique IDs** - Enable idempotent retries
8. **Log transitions** - Debug saga failures

## Common Patterns

### Saga with Multiple Services

```python
# Service A: Account Service
async def debit_external(account_id: str, amount: float) -> dict:
    response = await http_client.post(
        f"https://account-service/debit",
        json={"account_id": account_id, "amount": amount}
    )
    return response.json()

# Saga coordinates across services
saga = Saga("TransferMoney", [
    SagaStep(name="debit", action=debit_external),
    SagaStep(name="credit", action=credit_external),
], state_store)
```

### Saga with Retries

```python
from orchestrix.core import RetryPolicy

# Add retry logic to steps
async def reliable_debit(account_id: str, amount: float, **kwargs):
    retry_policy = RetryPolicy(max_retries=3, backoff_ms=100)
    
    for attempt in range(retry_policy.max_retries):
        try:
            return await debit_account(account_id, amount)
        except TemporaryError:
            if attempt < retry_policy.max_retries - 1:
                await asyncio.sleep(retry_policy.backoff_ms / 1000)
            else:
                raise
```

### Saga with Timeout

```python
async def step_with_timeout(account_id: str, amount: float, **kwargs):
    try:
        return await asyncio.wait_for(
            debit_account(account_id, amount),
            timeout=5.0  # 5 second timeout
        )
    except asyncio.TimeoutError:
        raise ValueError(f"Debit operation timed out")
```

## Production Considerations

### 1. State Persistence

Replace `InMemorySagaStateStore` with database:

```python
class PostgresSagaStateStore:
    async def load_state(self, saga_id: str) -> Optional[SagaState]:
        # Query from PostgreSQL
        pass
    
    async def save_state(self, state: SagaState) -> None:
        # Insert/update in PostgreSQL
        pass
```

### 2. Monitoring

Track saga metrics:

```python
# Number of sagas by status
sagas_completed = count(status=COMPLETED)
sagas_failed = count(status=FAILED)

# Average execution time
avg_duration = mean(completed_at - started_at)

# Compensation frequency
compensation_rate = count(compensation_executed) / count(total_sagas)
```

### 3. Dead Letter Queue

Handle permanently failed sagas:

```python
if saga.status == FAILED and compensation_failed:
    await dead_letter_queue.publish({
        "saga_id": saga.saga_id,
        "error": saga.error,
        "last_step": saga.current_step
    })
    # Manual intervention needed
```

### 4. Recovery

Recover crashed sagas:

```python
# On startup
for saga_id in unfinished_sagas():
    saga = await load_saga(saga_id)
    if saga.status == IN_PROGRESS:
        # Retry compensation or resume
        try:
            await saga.execute()
        except:
            # Still failing, escalate
            pass
```

## Testing

```bash
pytest tests/test_saga.py -v
```

Key test scenarios:

- ✓ Successful execution (all steps complete)
- ✓ Step failure (compensation triggered)
- ✓ Compensation order (reverse sequence)
- ✓ State persistence (recovery)
- ✓ Multiple sagas (independence)
- ✓ Idempotent execution

## References

- [Saga Pattern (Chris Richardson)](https://chrisrichardson.net/post/microservices/2019/07/09/developing-sagas-part-1.html)
- [Event Sourcing + CQRS + Sagas](https://particular.net/blog/sagas-orchestration-patterns)
- [Orchestrix Documentation](../../docs/)

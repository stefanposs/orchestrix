# Orchestrix Documentation Audit Report

**Date:** 2026-02-06  
**Scope:** All 26 mkdocs pages in `assets/mkdocs/` vs. actual source code  
**Severity Legend:** 🔴 WRONG (factually incorrect/broken) | 🟡 MISSING (undocumented features) | 🔵 IMPROVEMENT (quality enhancement)

---

## Table of Contents

1. [demos/banking.md](#1-demosbankingmd)
2. [demos/ecommerce.md](#2-demosecommercemd)
3. [demos/events_and_commands.md](#3-demosevents_and_commandsmd)
4. [demos/notifications.md](#4-demosnotificationsmd)
5. [demos/projection.md](#5-demosprojectionmd)
6. [demos/tracing.md](#6-demostracingmd)
7. [demos/validation.md](#7-demosvalidationmd)
8. [demos/versioning.md](#8-demosversioningmd)
9. [demos/gcp_demo.md](#9-demosgcp_demomd)
10. [getting-started/installation.md](#10-getting-startedinstallationmd)
11. [getting-started/quick-start.md](#11-getting-startedquick-startmd)
12. [getting-started/concepts.md](#12-getting-startedconceptsmd)
13. [guide/index.md](#13-guideindexmd)
14. [guide/creating-modules.md](#14-guidecreating-modulesmd)
15. [guide/commands-events.md](#15-guidecommands-eventsmd)
16. [guide/message-bus.md](#16-guidemessage-busmd)
17. [guide/event-store.md](#17-guideevent-storemd)
18. [guide/production-deployment.md](#18-guideproduction-deploymentmd)
19. [guide/production-ready.md](#19-guideproduction-readymd)
20. [guide/best-practices.md](#20-guidebest-practicesmd)
21. [api/core.md](#21-apicoremd)
22. [api/infrastructure.md](#22-apiinfrastructuremd)
23. [development/architecture.md](#23-developmentarchitecturemd)
24. [development/contributing.md](#24-developmentcontributingmd)
25. [development/testing.md](#25-developmenttestingmd)
26. [architecture/ASYNC_DESIGN.md](#26-architectureasync_designmd)

---

## 1. demos/banking.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Source code paths (all links)** | `bases/orchestrix/banking/` | `bases/orchestrix/banking_demo/` |
| 2 | **Run command** | `uv run python bases/orchestrix/banking/main.py` | `uv run python -m bases.orchestrix.banking_demo.main` |
| 3 | **Usage example imports** | `from examples.banking.aggregate import Account` | `from bases.orchestrix.banking_demo.aggregate import Account` (or relative `.aggregate`) |
| 4 | **Usage example imports** | `from examples.banking.handlers import register_handlers` | `from bases.orchestrix.banking_demo.handlers import register_handlers` |
| 5 | **Usage example imports** | `from examples.banking.models import OpenAccount, TransferMoney` | `from bases.orchestrix.banking_demo.models import OpenAccount, TransferMoney` |
| 6 | **Usage example imports** | `from examples.banking.saga import register_saga` | `from bases.orchestrix.banking_demo.saga import register_saga` |
| 7 | **Infrastructure imports** | `from orchestrix.infrastructure.memory import InMemoryEventStore, InMemoryMessageBus` | Actual banking main.py uses `from orchestrix.infrastructure.memory.utils import InMemoryEventStore, InMemoryMessageBus` |
| 8 | **Bus method** | `message_bus.publish_async(...)` | Actual main.py uses `message_bus.publish(...)` (the async version) |
| 9 | **Repository construction** | `AggregateRepository(event_store)` | Actual: `AggregateRepository[Account](event_store)` (generic typed) |
| 10 | **WithdrawMoney command fields** | Has `transaction_id: str` | Actual `WithdrawMoney` has no `transaction_id` — only `account_id`, `amount`, `description` |
| 11 | **DepositMoney command fields** | Has `transaction_id: str` | Actual `DepositMoney` has no `transaction_id` — only `account_id`, `amount`, `description` |
| 12 | **Account aggregate** | Shows `status: AccountStatus` and methods `withdraw(amount, txn_id, description)` | Actual aggregate `withdraw(amount, transaction_id, description)` takes `transaction_id` as parameter but it comes from the handler, not the Command |
| 13 | **Bottom source links** | `bases/orchestrix/banking/aggregate.py` etc. | Should be `bases/orchestrix/banking_demo/aggregate.py` |
| 14 | **Projection example** | `event.data.amount`, `event.data.description` | Events don't have a `.data` wrapper — fields are directly on the event: `event.amount`, `event.description` |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `SuspendAccount`, `ReactivateAccount` commands exist | Not mentioned |
| 2 | `AccountSuspended`, `AccountReactivated`, `AccountClosed` events exist | Not mentioned |
| 3 | Account aggregate extends `AggregateRoot` with `_apply_event()`, `_when_*()` pattern | Doc shows manual event list pattern instead |
| 4 | `validated_example.py` exists in ecommerce_demo (adjacent demo) | Not referenced |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Show actual `AggregateRoot` base class pattern with `_when_*()` handlers instead of manual list approach |
| 2 | Add link to run with `just` command if available |
| 3 | Fix "Related Examples" link `lakehouse.md` — verify the file exists |

---

## 2. demos/ecommerce.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **All source links** | `examples/ecommerce/` | `bases/orchestrix/ecommerce_demo/` |
| 2 | **Run command** | `uv run python bases/orchestrix/ecommerce/example.py` | `uv run python -m bases.orchestrix.ecommerce_demo.main` |
| 3 | **All import paths in Usage** | `from examples.ecommerce.*` | `from bases.orchestrix.ecommerce_demo.*` |
| 4 | **CreateOrder definition** | `@dataclass(frozen=True, kw_only=True)` with `shipping_address: Address` | Actual: `@dataclass(frozen=True)` (no `kw_only`) |
| 5 | **ProcessPayment fields** | `order_id`, `amount`, `payment_method: str` | Actual: `order_id`, `payment_id`, `amount`, `method` (different field names) |
| 6 | **ReserveInventory fields** | `order_id`, `items: list[OrderItem]` | Actual: need to verify, but the doc omits `reservation_id` |
| 7 | **Order aggregate methods** | `order.create(...)`, `order.complete_payment(payment_id)` | Actual: `order.create(order_id, customer_id, items, shipping_address)` and `order.complete_payment(payment_id, transaction_id, amount)` — more params |
| 8 | **Missing events** | Docs mention `PaymentProcessing` event | Actual event is `PaymentInitiated`, not `PaymentProcessing` |
| 9 | **Usage example** | `AggregateRepository(event_store)` | `AggregateRepository[Order](event_store)` |
| 10 | **Bottom source links** | `examples/ecommerce/aggregate.py` etc. | `bases/orchestrix/ecommerce_demo/aggregate.py` |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `OrderItem.total_price` computed property | Not shown |
| 2 | `PaymentDetails` value object | Not documented |
| 3 | `PaymentStatus` enum | Not documented |
| 4 | `OrderCompleted` event, `InventoryReleased` event, `PaymentRefunded` event | Listed but not shown with fields |
| 5 | `validated_example.py` file | Not mentioned |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Show the actual `AggregateRoot` + `_when_*()` pattern used in code |
| 2 | Document the actual saga step naming (method signatures) |
| 3 | "Related Examples" links to `lakehouse.md` — verify |

---

## 3. demos/events_and_commands.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Imports** | `from orchestrix import Command, Event` | Actual demo: `from orchestrix.core.messaging import Command, Event` |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | Source file path | No `📂 Source Code` box — actual file is `bases/orchestrix/events_and_commands_demo/demo_events_and_commands.py` |
| 2 | `simple_module/` subdirectory | Exists in demo dir but not mentioned |
| 3 | Run command | No run command provided |
| 4 | The actual demo only defines the dataclasses then has a comment — no bus usage | Could show bus integration |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Add source code box with correct GitHub link |
| 2 | Add run command |
| 3 | Show a complete working example with bus.publish() |

---

## 4. demos/notifications.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **All source links** | `examples/notifications/` | `bases/orchestrix/notifications_demo/` |
| 2 | **Run command** | `uv run python bases/orchestrix/notifications/example.py` | `uv run python -m bases.orchestrix.notifications_demo.main` |
| 3 | **All import paths** | `from examples.notifications.*` | `from bases.orchestrix.notifications_demo.*` |
| 4 | **SendNotification `subject` field** | `subject: Optional[str] = None` | Actual: `subject: str` (required, not Optional) |
| 5 | **SendNotification `metadata` field** | `metadata: dict = field(default_factory=dict)` | Actual: `metadata: dict[str, Any] \| None = None` |
| 6 | **datetime import** | `datetime.now(timezone.utc)` | Actual uses `datetime.now(UTC)` with `from datetime import UTC` |
| 7 | **Handler property** | `handler.sent_notifications` | Actual property name not verified — doc may be fabricated |
| 8 | **DLQ message access** | `dlq_message.notification_id`, `dlq_message.failure_reason` | Needs verification vs actual `DeadLetteredMessage` shape |
| 9 | **Subscriber decorator** | `@message_bus.subscribe(OrderPlaced)` (decorator syntax) | Actual bus uses `bus.subscribe(EventType, handler_func)` — no decorator form |
| 10 | **Bottom link** | `examples/notifications` | `bases/orchestrix/notifications_demo` |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `NotificationRequested` event | Exists in models but not shown |
| 2 | `NotificationRetrying` event | Exists in models but not shown |
| 3 | `NotificationStatus` enum | Exists but not documented |
| 4 | Overview bullet points are empty | "The notifications example demonstrates:" has no list items |
| 5 | Dead Letter Queue section is empty | "Failed notifications after max retries are moved to DLQ for:" has no list items |
| 6 | "Domain Events (trigger notifications):" is empty | Missing list |
| 7 | "Notification Events:" is empty | Missing list |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Fill in all the empty list sections |
| 2 | Show the actual `RetryConfig` from handlers, not a custom one |
| 3 | Remove the `CircuitBreaker` example — it doesn't exist in code and is misleading |

---

## 5. demos/projection.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Import** | `from orchestrix import InMemoryMessageBus, Event` | Actual: `from orchestrix.infrastructure.memory import InMemoryMessageBus` and `from orchestrix.core.messaging import Event` (separate imports) |
| 2 | **Example pattern** | Simple dict-based `user_emails = {}` with inline lambda | Actual demo uses `AccountProjection` class with typed `apply_*` methods and `AccountCreated`, `MoneyDeposited`, `MoneyWithdrawn` events |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | Source file path | `bases/orchestrix/projection_demo/demo_projection.py` — not referenced |
| 2 | `AccountProjection` class | The actual sophisticated projection class isn't shown |
| 3 | `ProjectionEngine`, `ProjectionState`, `ProjectionEventHandler` in `components/orchestrix/core/eventsourcing/projection.py` | Entire projection framework undocumented |
| 4 | Run command | None provided |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Show the actual demo code or at least accurately reflect the pattern |
| 2 | Document the `projection.py` module in the core API reference |
| 3 | Add source code box and run command |

---

## 6. demos/tracing.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Imports** | `from orchestrix import InMemoryMessageBus, Command, Event` | Should be `from orchestrix.infrastructure.memory import InMemoryMessageBus` and `from orchestrix.core.messaging import Command, Event` |
| 2 | **No demo source exists** | Doc suggests a working tracing demo | `projects/tracing_demo/` only has `README.md` and `pyproject.toml` — **no actual source code** |
| 3 | **Command subscription** | `bus.subscribe(MyCommand, lambda cmd: ...)` | The sync bus accepts commands via subscribe, but this is unusual — typically commands go to one handler |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `TraceSpan`, `TracingProvider` in `components/orchestrix/core/common/observability.py` | Entire tracing infrastructure undocumented |
| 2 | OpenTelemetry integration built into observability module | Not mentioned beyond a vague suggestion |
| 3 | `trace_id` field on `Message` base class | Not shown |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Either create an actual tracing demo or mark this page as "planned" |
| 2 | Document the actual `TracingProvider`, `TraceSpan` APIs |
| 3 | Show real OpenTelemetry integration example |

---

## 7. demos/validation.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Import** | `from orchestrix import Command` | Should be `from orchestrix.core.messaging import Command` (or `Event` — see #2) |
| 2 | **Message type** | Validates a `RegisterUser(Command)` | Actual demo validates `UserRegistered(Event)` — uses Event, not Command |
| 3 | **Fields** | `user_id`, `email`, `password` | Actual: `email`, `age`, `username` (completely different fields) |
| 4 | **Validation approach** | `__post_init__` inside the dataclass | Actual uses external `validate_user_registered()` function |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | Source file path | `bases/orchestrix/validation_demo/demo_validation.py` — not referenced |
| 2 | `ValidationError` custom exception class (in demo) | Not shown |
| 3 | `components/orchestrix/core/common/validation.py` module | Entire validation utility module (`validate_not_empty`, `validate_positive`, `validate_min_length`, etc.) undocumented |
| 4 | Run command | None provided |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Show both validation approaches: `__post_init__` AND external validator function |
| 2 | Document the built-in validation utilities from `core/common/validation.py` |
| 3 | Match the actual demo code |

---

## 8. demos/versioning.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Import** | `from orchestrix import Event` | Should be `from orchestrix.core.messaging import Event` |
| 2 | **Versioning approach** | Redefines same class `UserCreated(Event)` twice (overwrites) | Actual demo uses `UserCreatedV1(Event)` and `UserCreatedV2(Event)` — **separate classes with explicit version names** |
| 3 | **Pattern shown** | Backward-compatible single class with defaults | Actual pattern is **multi-handler strategy** with distinct event types per version |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | Source file path | `bases/orchestrix/versioning_demo/demo_versioning.py` — not referenced |
| 2 | `EventUpcast` protocol, `EventUpcaster` class, `UpcasterRegistry` | Entire upcasting framework in `components/orchestrix/core/eventsourcing/versioning.py` is undocumented |
| 3 | `VersionedEvent` dataclass | Not documented |
| 4 | Multi-handler strategy with bus routing | Actual demo shows bus routing both V1 and V2 events to separate handlers |
| 5 | Run command | None provided |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Show both approaches: simple defaults AND the multi-handler/upcaster pattern |
| 2 | Document the full upcasting framework from `versioning.py` |
| 3 | Match actual demo code pattern |

---

## 9. demos/gcp_demo.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Only CloudSQL** | Shows only CloudSQL demo | Actual `main.py` also includes `GCPBigQueryEventStore` demo |
| 2 | **Store method** | `await store.append("demo-stream", {...})` / `store.load("demo-stream")` | Need to verify actual store API — the CloudSQLStore is aliased as `GCPCloudSQLEventStore` |
| 3 | **Missing env var guidance** | "see README in the gcp_cloud_sql folder" | Should list actual required env vars |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | BigQuery event store demo | `bigquery_demo()` function exists but not shown |
| 2 | `GCPBigQueryEventStore` import | Not even mentioned |
| 3 | `pubsub_demo.py` file | Exists in `bases/orchestrix/gcp_demo/` but not documented |
| 4 | GCP Pub/Sub infrastructure | `components/orchestrix/infrastructure/gcp_pubsub/` exists |
| 5 | Source file path | No reference to `bases/orchestrix/gcp_demo/main.py` |
| 6 | Run command | Not provided |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Document all three GCP integrations: CloudSQL, BigQuery, Pub/Sub |
| 2 | Add source code box and run command |
| 3 | List required environment variables explicitly |

---

## 10. getting-started/installation.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Optional extras** | `pip install orchestrix[postgres]`, `orchestrix[observability]`, `orchestrix[postgres,observability]` | **No extras defined in pyproject.toml** — the package just ships all dependencies |
| 2 | **Verify installation** | `import orchestrix; print(orchestrix.__version__)` | `components/orchestrix/__init__.py` is effectively empty — no `__version__` attribute |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | Actual dependencies list | Not shown (asyncpg, eventsourcingdb, prometheus_client, psycopg, pydantic, fastapi, httpx, etc.) |
| 2 | Python version requirement | Doc says "3.12 or higher", pyproject.toml says `>=3.12,<3.14` — upper bound missing from doc |
| 3 | Polylith workspace structure | Not explained for developers wanting to understand the repo layout |
| 4 | `uv sync` vs `uv add` distinction | Not clarified |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Either define extras in pyproject.toml OR remove extras from docs |
| 2 | Add `__version__` to `__init__.py` or remove the verify step |
| 3 | Document the upper Python version bound (`<3.14`) |

---

## 11. getting-started/quick-start.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **All top-level imports** | `from orchestrix import Command, Event`, `from orchestrix import CommandHandler, MessageBus, EventStore`, `from orchestrix import Module`, `from orchestrix import InMemoryMessageBus, InMemoryEventStore` | These **do not exist** at `orchestrix` top-level. Correct: `from orchestrix.core.messaging import Command, Event`, `from orchestrix.core.messaging import CommandHandler`, `from orchestrix.core.messaging.message_bus import MessageBus`, `from orchestrix.core.eventsourcing.event_store import EventStore`, `from orchestrix.core.common.module import Module`, `from orchestrix.infrastructure.memory import InMemoryMessageBus, InMemoryEventStore` |
| 2 | **`CommandHandler[CreateTask]`** | Used as generic base class to inherit from | `CommandHandler` is a `Protocol`, not an inheritable generic class |
| 3 | **`store.save(id, events)` / `store.load(id)`** | Simple positional calls | Actual EventStore has `save(aggregate_id, events, expected_version=None)` and `load(aggregate_id, from_version=0)` |
| 4 | **Broken link** | `[GDPR Lakehouse](../demos/lakehouse.md)` | File exists but should verify content |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `AggregateRoot` base class | The actual way to build aggregates uses `AggregateRoot` with `_apply_event()` — NOT manual `_events` list |
| 2 | `AggregateRepository` | Key class for loading/saving aggregates is not mentioned |
| 3 | Async API | Quick start shows only sync — should at least mention async exists |
| 4 | Getting started demo file | `bases/orchestrix/getting_started_demo/demo_getting_started.py` exists and is simpler |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Use the actual `AggregateRoot` pattern from the codebase |
| 2 | Show the real getting_started_demo as the quick start example |
| 3 | Fix all import paths to be real, working imports |

---

## 12. getting-started/concepts.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **All imports** | `from orchestrix import ...` | Wrong top-level path (same as quick-start) |
| 2 | **Message `timestamp` type** | Implied as `str` | Actual: `datetime` object (`datetime.now(UTC)`) |
| 3 | **Message fields** | Shows `id`, `type`, `source`, `timestamp` | Actual has 12 fields: `id`, `specversion`, `type`, `source`, `timestamp`, `subject`, `data`, `datacontenttype`, `dataschema`, `correlation_id`, `causation_id`, `trace_id` |
| 4 | **`CommandHandler[CreateOrder]`** | Generic base class | `CommandHandler` is a Protocol, not generic |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | CloudEvents v1.0 specification fields | `specversion`, `subject`, `data`, `datacontenttype`, `dataschema` |
| 2 | Causation/correlation tracking | `correlation_id`, `causation_id`, `trace_id` |
| 3 | `AggregateRoot` base class | Not mentioned |
| 4 | `AggregateRepository` | Not mentioned |
| 5 | Async bus and store | Not mentioned |
| 6 | `Saga` execution framework | Not mentioned |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Show the actual full `Message` class with all CloudEvents fields |
| 2 | Mention the async-first nature of the framework |

---

## 13. guide/index.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Contact email** | `stefan@example.com` | Should be `sp@stefanposs.com` (per pyproject.toml) |
| 2 | **Docs URL** | `https://orchestrix.readthedocs.io` | Needs verification — may not exist |
| 3 | **Path 2 link** | `[Demos: Observability](../demos/projection.md)` | Projection demo is not about observability |
| 4 | **Path 3 link** | `[Demos: Performance](../demos/projection.md)` | Projection demo is not about performance |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | Lakehouse demo link | Not in the navigation — this is the most feature-rich demo |
| 2 | Web GUI demo | Fully built Dash app exists but isn't mentioned anywhere |
| 3 | GCP demo | Only in demos nav, not in reading paths |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Add Lakehouse and Web GUI demos to reading paths |
| 2 | Fix or remove readthedocs.io link |
| 3 | Fix email address |

---

## 14. guide/creating-modules.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **All imports** | `from orchestrix import Module, MessageBus, EventStore`, `from orchestrix import CommandHandler` | Wrong top-level paths |
| 2 | **`CommandHandler[CreateOrder]`** | Inheritable generic | `CommandHandler` is a Protocol |
| 3 | **Module.register signature** | `register(self, bus: MessageBus, store: EventStore)` | This is correct per the Protocol, but imports to get `MessageBus` and `EventStore` are wrong |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | Actual Polylith module structure | The repo uses Polylith architecture (components/, bases/, projects/) — not the flat structure shown |
| 2 | Async module registration | Not mentioned |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Show the actual Polylith layout alongside the generic layout |
| 2 | Fix import paths throughout |

---

## 15. guide/commands-events.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **All imports** | `from orchestrix import Command`, `from orchestrix import Event` | Wrong path; should be `from orchestrix.core.messaging import Command, Event` |

### 🟡 MISSING — (none significant)

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Fix import paths |
| 2 | Mention the `kw_only=True` convention used in actual events (most real events use it) |
| 3 | Mention `correlation_id`, `causation_id` for event chaining |

---

## 16. guide/message-bus.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Imports** | `from orchestrix import InMemoryMessageBus, Command, Event` | Wrong path |
| 2 | **Error handling behavior** | "Der InMemoryMessageBus hat **keine eingebaute Error Handling**" and "Wird nicht aufgerufen!" (subsequent handlers not called) | **WRONG**: Actual `InMemoryMessageBus` catches exceptions per handler, logs them, and **continues** to other handlers. Only raises `HandlerError` if ALL handlers fail. |
| 3 | **Implementation shown** | Simple `defaultdict(list)` with no error handling | Actual implementation has structured logging, `HandlerError` wrapping, continuation on individual handler failure |
| 4 | **`CommandHandler[CreateOrder]`** | Generic class | Protocol |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `InMemoryAsyncMessageBus` | Complete async bus with `asyncio.gather()` — fully implemented but not documented in this page |
| 2 | `HandlerError` exception | Used in actual bus but not mentioned |
| 3 | Structured logging (`StructuredLogger`) | Built into bus but undocumented |
| 4 | `utils.py` compatibility shim | `InMemoryMessageBus` from `utils` is actually the async bus with aliases |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | **Fix the error handling section** — this is the most dangerous misinformation |
| 2 | Document the async message bus |
| 3 | Write in consistent language (currently mixed German/English) |

---

## 17. guide/event-store.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Import** | `from orchestrix import InMemoryEventStore` | Wrong path: `from orchestrix.infrastructure.memory import InMemoryEventStore` |
| 2 | **EventStore interface** | `save(aggregate_id, events)` and `load(aggregate_id)` | Actual: `save(aggregate_id, events, expected_version=None)` and `load(aggregate_id, from_version=0)` |
| 3 | **Implementation shown** | Simple defaultdict, no concurrency control | Actual has `ConcurrencyError`, optimistic locking via `expected_version`, snapshot support, trace-id indexing |
| 4 | **`get_all_aggregate_ids()`** | Shown in replay example | This method does NOT exist on InMemoryEventStore |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | Snapshot support in InMemoryEventStore | `save_snapshot()`, `load_snapshot()` — built in |
| 2 | `InMemoryAsyncEventStore` | Async version exists |
| 3 | `PostgreSQLEventStore` | Production store exists but not documented here |
| 4 | `Snapshot` dataclass | Full snapshot model exists |
| 5 | Trace-based event loading | `load_by_trace(trace_id)` method |
| 6 | Optimistic concurrency with `ConcurrencyError` | Key feature exists |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Show the actual interface including `expected_version` and `from_version` |
| 2 | Document snapshot and async stores |
| 3 | Mention `PostgreSQLEventStore` and `EventSourcingDB` store |

---

## 18. guide/production-deployment.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Import path** | `from orchestrix.infrastructure import InMemoryMessageBus, InMemoryEventStore` | Correct: `from orchestrix.infrastructure.memory import ...` |
| 2 | **PostgreSQL class name** | `PostgresEventStore` | Actual: `PostgreSQLEventStore` |
| 3 | **PostgreSQL import** | `from orchestrix.infrastructure import PostgresEventStore, ConnectionPool` | No `ConnectionPool` class. Correct: `from orchestrix.infrastructure.postgres.store import PostgreSQLEventStore` |
| 4 | **PostgreSQL constructor** | `PostgresEventStore(pool)` | Actual: `PostgreSQLEventStore(connection_string="...", pool_min_size=10, pool_max_size=50, pool_timeout=30.0)` |
| 5 | **AggregateRepository constructor** | `AggregateRepository(store=store, snapshot_frequency=50)` | Actual: `AggregateRepository(event_store)` — no `snapshot_frequency` param, no `store=` kwarg |
| 6 | **Observability hooks** | `bus.add_observability_hook(metrics)`, `store.add_observability_hook(metrics)` | These methods **do not exist** |
| 7 | **PrometheusMetrics import** | `from orchestrix.infrastructure import PrometheusMetrics` | No such class at this path |
| 8 | **AggregateRepository import** | `from orchestrix.core import AggregateRepository` | Correct: `from orchestrix.core.eventsourcing.aggregate import AggregateRepository` |
| 9 | **PostgreSQL driver** | Doc implies `asyncpg` only | Actual lib package uses `psycopg[binary]`, not asyncpg (workspace uses asyncpg) |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `PostgreSQLEventStore.initialize()` required call | Must call `await store.initialize()` before use |
| 2 | EventSourcingDB store | Exists in `components/orchestrix/infrastructure/eventsourcingdb/` |
| 3 | Auto-migration for Postgres | `_ensure_schema()` is internal — no `orchestrix migrate` CLI exists |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Fix all class names and constructors to match actual API |
| 2 | Show actual PostgreSQLEventStore initialization flow |
| 3 | Remove fabricated methods like `add_observability_hook` |

---

## 19. guide/production-ready.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **PostgreSQL class** | `PostgresEventStore(connection_string=..., pool_size=20)` | `PostgreSQLEventStore(connection_string=..., pool_min_size=10, pool_max_size=50)` |
| 2 | **EventSourcingDB class** | `EventSourcingDBStore(url=..., stream_name=...)` | Actual class may differ — module exists at `infrastructure/eventsourcingdb/store.py` |
| 3 | **SnapshotStore** | `InMemorySnapshotStore()` as separate class | **Does not exist** as a separate class. Snapshots are integrated into `InMemoryEventStore` and `InMemoryAsyncEventStore` |
| 4 | **AggregateRepository** | `AggregateRepository(event_store=..., snapshot_store=..., snapshot_interval=100)` | Actual: `AggregateRepository(event_store)` — no snapshot_store param, no snapshot_interval |
| 5 | **CLI command** | `orchestrix migrate` | **No CLI exists** |
| 6 | **Observability init** | `from orchestrix.core.common.observability import init_observability` | No `init_observability` function — module has `MetricsProvider`, `TracingProvider` ABCs |
| 7 | **Setup** | `python3.13 -m venv venv` | Should also mention `uv` (recommended per project) |
| 8 | **Env file** | `cp .env.example .env` | No `.env.example` file exists in the repo |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `MetricsProvider` ABC with `counter()`, `gauge()`, `histogram()` methods | The actual observability API |
| 2 | `TracingProvider` ABC | For distributed tracing |
| 3 | `TraceSpan` dataclass | For span tracking |
| 4 | `LoggingMetricsProvider` built-in impl | Exists in observability module |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Rewrite the Configuration section with actual constructor signatures |
| 2 | Create a `.env.example` file or remove that reference |
| 3 | Show actual observability integration with real class names |

---

## 20. guide/best-practices.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Imports** | `from orchestrix import ...` everywhere | Wrong top-level paths |
| 2 | **`CommandHandler[CreateOrder]`** | Generic class | Protocol |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `AggregateRoot` usage patterns | Not shown — all examples use manual aggregate patterns |
| 2 | Built-in retry policies | `ExponentialBackoff`, `NoRetry` in `core/common/retry.py` |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Fix imports |
| 2 | Write in consistent language (mixed German/English) |
| 3 | Show actual `AggregateRoot` + `_when_*()` pattern as best practice |

---

## 21. api/core.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Message class fields** | `id`, `type`, `source`, `timestamp` (4 fields) | Actual has 12 fields including `specversion`, `subject`, `data`, `datacontenttype`, `dataschema`, `correlation_id`, `causation_id`, `trace_id` |
| 2 | **`timestamp` type** | `str` with `datetime.utcnow().isoformat()` | Actual: `datetime` type with `datetime.now(UTC)` |
| 3 | **`datetime.utcnow()`** | Used in default factory | **Deprecated** in Python 3.12+. Actual code uses `datetime.now(UTC)` |
| 4 | **EventStore Protocol** | `save(aggregate_id, events)` and `load(aggregate_id)` | Actual: `save(aggregate_id, events, expected_version=None)` and `load(aggregate_id, from_version=0)` |
| 5 | **CommandHandler** | `CommandHandler(Protocol)` with `__init__(bus, store)` and shown as generic `CommandHandler[T]` | Actual Protocol has `handle(command: Command)` and `_persist_and_publish(aggregate_id, events)` — NOT generic |
| 6 | **`kw_only`** | Not shown on `Message` | Actual `Message` uses `@dataclass(frozen=True, kw_only=True)` |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `AsyncMessageBus` Protocol | Exists in `message_bus.py` |
| 2 | `AsyncEventStore` Protocol | Exists in `event_store.py` |
| 3 | `AggregateRoot` class | Core class for building aggregates |
| 4 | `AggregateRepository` class | Core class for persistence |
| 5 | `Snapshot` dataclass | For snapshot support |
| 6 | `SagaStatus`, `SagaStepStatus`, `SagaState` | Saga framework |
| 7 | `DeadLetterQueue`, `DeadLetteredMessage` | DLQ framework |
| 8 | `RetryPolicy`, `ExponentialBackoff`, `NoRetry` | Retry policies |
| 9 | `ValidationError`, validation utilities | Built-in validation |
| 10 | `ProjectionState`, `ProjectionEventHandler` | Projection framework |
| 11 | `EventUpcast`, `EventUpcaster`, `UpcasterRegistry` | Versioning framework |
| 12 | `Module` Protocol | Module abstraction |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | This is the most critical page to fix — document ALL actual Protocol definitions |
| 2 | Use mkdocstrings to auto-generate from source |
| 3 | Organize by submodule: messaging, eventsourcing, execution, common |

---

## 22. api/infrastructure.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Import** | `from orchestrix import InMemoryMessageBus` | Should be `from orchestrix.infrastructure.memory import InMemoryMessageBus` |
| 2 | **Error behavior** | "If a handler raises an exception, subsequent handlers are **not** called" | **WRONG**: Actual behavior catches per-handler exceptions and **continues**. Only raises if ALL handlers fail. |
| 3 | **Implementation details** | States "No transaction management or error recovery" | Actual HAS error recovery — wraps each handler in try/except |
| 4 | **Broken code block** | The `subscribe` examples section has a malformed `CreateOrderHandler.handle()` definition floating outside a class | Formatting error |
| 5 | **Import** | `from orchestrix import InMemoryEventStore` | `from orchestrix.infrastructure.memory import InMemoryEventStore` |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `InMemoryAsyncMessageBus` | Entire async bus |
| 2 | `InMemoryAsyncEventStore` | Entire async store |
| 3 | `utils.py` compatibility layer | Alias classes with `_async` method aliases |
| 4 | `PostgreSQLEventStore` | Production Postgres store |
| 5 | `CloudSQLStore` (GCP CloudSQL) | GCP store |
| 6 | `GCPBigQueryEventStore` | BigQuery store |
| 7 | EventSourcingDB store | Third-party event store integration |
| 8 | Snapshot methods on stores | `save_snapshot()`, `load_snapshot()` |
| 9 | `load_by_trace()` | Trace-based event querying |
| 10 | `ConcurrencyError` | Thrown on optimistic lock failures |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | **Critical: Fix error handling description** — this misleads users about fault tolerance |
| 2 | Document ALL store implementations |
| 3 | Fix the broken code formatting |

---

## 23. development/architecture.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Version** | "Current (v0.1.0)" — labels sync-only as current | Async IS already implemented, not "Future" |
| 2 | **"Future Scaling" async** | Shows `AsyncMessageBus` as future plan | Already exists at `infrastructure/memory/async_bus.py` |
| 3 | **Protocol implementation** | Shows simplified `InMemoryMessageBus` with no error handling | Actual has structured logging and error handling |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `AggregateRoot` with `_when_*()` dispatch | Core pattern not shown |
| 2 | Saga orchestration module | `core/execution/saga.py` |
| 3 | Observability hooks | Built-in metrics/tracing |
| 4 | Polylith architecture | How components/bases/projects relate |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Update "Current" section to reflect async-first reality |
| 2 | Add Polylith architecture explanation |
| 3 | Consistent language (mixed German/English) |

---

## 24. development/contributing.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **CI Python versions** | "Tests auf Python 3.9-3.13" | `requires-python = ">=3.12,<3.14"` — only 3.12-3.13 |
| 2 | **Example file path** | `vim components/orchestrix.core.messaging.message_bus.py` (dots) | Should be `vim components/orchestrix/core/messaging/message_bus.py` (slashes) |
| 3 | **Coverage** | "100% required" | Not enforced — no `fail_under` in pytest config and current coverage not specified |
| 4 | **Tools** | "black" and "isort" mentioned | Both are in dev deps but `ruff` handles both — docs should clarify ruff replaces them |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `testcontainers` setup | Mentioned at top but not woven into the main Contributing section well |
| 2 | `.container-versions.json` | Referenced but not shown example |
| 3 | `ty` (type checker) in dev deps | Not mentioned |
| 4 | `just` command reference is good | ✅ Correct |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Fix Python version range |
| 2 | Fix file path (dots → slashes) |
| 3 | Consistent language (mixed German/English) |
| 4 | Add note about Polylith workflow |

---

## 25. development/testing.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Test directory** | `tests/` | Actual: `test/` (no trailing 's') |
| 2 | **Test structure** | `tests/unit/`, `tests/integration/`, `tests/performance/` | Actual: `test/components/`, `test/bases/`, `test/projects/`, `test/benchmarks/` |
| 3 | **Install command** | `pip install orchestrix[test]` | No `[test]` extra exists |
| 4 | **`CommandHandler[CreateOrder]`** | Generic class | Protocol |
| 5 | **Imports** | `from orchestrix import InMemoryMessageBus, InMemoryEventStore` | Wrong paths |
| 6 | **`command.type == "CreateOrder"`** attribute | Shown in test | Correct — `type` auto-derives from class name ✅ |
| 7 | **`FakeEventStore(EventStore)`** | Inherits from EventStore | `EventStore` is a Protocol — no inheritance needed, just implement methods |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `conftest.py` shared fixtures | Exists at `test/conftest.py` |
| 2 | `pytest-asyncio` usage | Tests use `asyncio_mode = "auto"` |
| 3 | `pytest-benchmark` | Benchmarks exist in `test/benchmarks/` |
| 4 | testcontainers integration tests | Postgres integration tests |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Fix directory structure to match actual `test/` layout |
| 2 | Show async test patterns with `pytest-asyncio` |
| 3 | Document benchmark testing |

---

## 26. architecture/ASYNC_DESIGN.md

### 🔴 WRONG

| # | Issue | Doc Says | Actual |
|---|-------|----------|--------|
| 1 | **Status** | "Design Phase" | Async is **fully implemented** — `InMemoryAsyncMessageBus`, `InMemoryAsyncEventStore`, `utils.py` shim all exist |
| 2 | **File paths** | `components/orchestrix/infrastructure/async_inmemory_bus.py` | Actual: `components/orchestrix/infrastructure/memory/async_bus.py` |
| 3 | **Test paths** | `tests/components/infrastructure/test_async_bus.py` | Actual test directory is `test/` not `tests/` |
| 4 | **Phase 1-3 roadmap** | Presented as future work | Phase 1 (parallel APIs) and Phase 2 (utils shim for mixing) are already done |

### 🟡 MISSING

| # | Feature in Code | Not Documented |
|---|----------------|----------------|
| 1 | `utils.py` backward-compatibility shim | Already implemented but not in this design doc |
| 2 | The actual async integration with `AggregateRepository.load_async()` and `save_async()` | Repository already detects sync/async stores |

### 🔵 IMPROVEMENTS

| # | Suggestion |
|---|-----------|
| 1 | Update status to "Implemented" with implementation notes |
| 2 | Add link to actual source files |
| 3 | Document what was implemented vs. what's still planned (e.g. Phase 3 unified API) |

---

## Global Issues (Across ALL Pages)

### 🔴 Systematic WRONG issues

| # | Issue | Affected Pages |
|---|-------|---------------|
| 1 | **`from orchestrix import X` doesn't work** — `components/orchestrix/__init__.py` is empty. All imports need full paths. | quick-start, concepts, all guides, all demos, all API pages |
| 2 | **`CommandHandler[T]` shown as inheritable generic** — it's a `Protocol` | quick-start, concepts, message-bus, creating-modules, best-practices, testing, api/core |
| 3 | **Demo paths use `examples/` or `bases/orchestrix/{name}/`** — actual paths are `bases/orchestrix/{name}_demo/` | banking, ecommerce, notifications, bottom links |

### 🟡 Systematic MISSING features

| # | Feature | Affected Pages |
|---|---------|---------------|
| 1 | **`AggregateRoot` + `_when_*()` dispatch pattern** — the cornerstone of the framework | All concept/guide pages show manual event lists instead |
| 2 | **`AggregateRepository`** — key persistence abstraction | Only mentioned in banking/ecommerce usage examples |
| 3 | **Saga framework** (`core/execution/saga.py`) — `SagaStatus`, `SagaState`, orchestration | Only alluded to in demos, never documented as API |
| 4 | **Full async API** — InMemoryAsyncMessageBus, InMemoryAsyncEventStore | Never documented, despite being fully implemented |
| 5 | **Observability framework** — `MetricsProvider`, `TracingProvider`, `TraceSpan` | Mentioned vaguely but never with actual API |
| 6 | **Retry framework** — `RetryPolicy`, `ExponentialBackoff`, `NoRetry` | Not documented |
| 7 | **Validation utilities** — `validate_not_empty`, `validate_positive`, etc. | Not documented |
| 8 | **Projection engine** — `ProjectionState`, `ProjectionEventHandler`, `ProjectionEngine` | Not documented |
| 9 | **Event upcasting** — `EventUpcast`, `EventUpcaster`, `UpcasterRegistry` | Not documented |
| 10 | **Dead letter queue** — `DeadLetterQueue`, `DeadLetteredMessage` | Not documented as API |
| 11 | **Lakehouse FastAPI demo** — most feature-rich demo | No dedicated docs page (only referenced as broken link) |
| 12 | **Web GUI demo** — full Dash dashboard | Completely undocumented |

### 🔵 Systematic IMPROVEMENTS

| # | Issue | Affected Pages |
|---|-------|---------------|
| 1 | **Mixed German/English** | message-bus, best-practices, contributing, architecture |
| 2 | **No auto-generated API docs** | Should use `mkdocstrings` with `::: orchestrix.core.messaging.message` directives |
| 3 | **No `__version__`** | Need to add to `__init__.py` |
| 4 | **No optional extras** | Need to define `[postgres]`, `[observability]`, `[test]` in pyproject.toml or remove from docs |
| 5 | **Stale "Design Phase" label** | ASYNC_DESIGN.md should reflect implemented status |

---

## Priority Fix Order

### P0 — Critical (blocks users)
1. Fix all import paths across ALL pages (`from orchestrix import X` → correct submodule paths)
2. Fix demo source code paths (`banking` → `banking_demo`, `examples/` → `bases/orchestrix/`)
3. Fix all run commands
4. Fix `InMemoryMessageBus` error handling description (currently says the opposite of reality)
5. Fix `CommandHandler` — it's a Protocol, not a generic base class

### P1 — High (misleads users)
1. Fix `PostgreSQLEventStore` class name and constructor everywhere
2. Fix `AggregateRepository` constructor (no snapshot_frequency, no snapshot_store)
3. Remove fabricated methods (`add_observability_hook`, `get_all_aggregate_ids`, etc.)
4. Fix `Message` class to show all 12 CloudEvents fields
5. Fix `EventStore`/`EventStore` protocol signatures (add `expected_version`, `from_version`)
6. Update ASYNC_DESIGN.md status to "Implemented"

### P2 — Medium (incomplete coverage)
1. Document `AggregateRoot` + `_when_*()` pattern across all relevant pages
2. Document async bus + store
3. Document `AggregateRepository`
4. Add API docs for saga, projection, retry, validation, versioning, DLQ modules
5. Create/fix demo pages for lakehouse, web GUI
6. Fill empty sections in notifications.md

### P3 — Low (polish)
1. Standardize language (all English or clearly marked German sections)
2. Add `__version__`, create `.env.example`
3. Define pyproject.toml extras or remove references
4. Fix contact email, readthedocs URL
5. Auto-generate API reference with mkdocstrings

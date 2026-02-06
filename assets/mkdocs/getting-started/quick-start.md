
# Quick Start

Build your first event-sourced application in 5 minutes.

## 1. Define Messages

```python
from dataclasses import dataclass
from orchestrix.core.messaging.message import Command, Event

@dataclass(frozen=True, kw_only=True)
class CreateTask(Command):
    task_id: str
    title: str

@dataclass(frozen=True, kw_only=True)
class TaskCreated(Event):
    task_id: str
    title: str

@dataclass(frozen=True, kw_only=True)
class CompleteTask(Command):
    task_id: str

@dataclass(frozen=True, kw_only=True)
class TaskCompleted(Event):
    task_id: str
```

## 2. Create an Aggregate

```python
from dataclasses import dataclass, field
from orchestrix.core.eventsourcing.aggregate import AggregateRoot

@dataclass
class Task(AggregateRoot):
    title: str = ""
    completed: bool = False

    def create(self, cmd: CreateTask):
        event = TaskCreated(task_id=cmd.task_id, title=cmd.title)
        self._apply_event(event)

    def complete(self, cmd: CompleteTask):
        if self.completed:
            raise ValueError("Already completed")
        event = TaskCompleted(task_id=cmd.task_id)
        self._apply_event(event)

    # _when methods — called automatically by _apply_event
    def _when_task_created(self, event: TaskCreated):
        self.aggregate_id = event.task_id
        self.title = event.title

    def _when_task_completed(self, event: TaskCompleted):
        self.completed = True
```

## 3. Wire Infrastructure & Run

```python
from orchestrix.core.eventsourcing.aggregate import AggregateRepository
from orchestrix.infrastructure.memory.store import InMemoryEventStore

store = InMemoryEventStore()
repo = AggregateRepository(event_store=store)

# Create a task
task = Task()
task.create(CreateTask(task_id="TASK-001", title="Learn Orchestrix"))
repo.save(task)

# Load and complete
task = repo.load(Task, "TASK-001")
task.complete(CompleteTask(task_id="TASK-001"))
repo.save(task)

print(f"Task: {task.title}, completed: {task.completed}")
# → Task: Learn Orchestrix, completed: True
```

## 4. Add Event Handlers (Optional)

```python
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus

bus = InMemoryMessageBus()
bus.subscribe(TaskCreated, lambda e: print(f"📝 Created: {e.title}"))
bus.subscribe(TaskCompleted, lambda e: print(f"✅ Completed: {e.task_id}"))

bus.publish(TaskCreated(task_id="TASK-002", title="Read the docs"))
# → 📝 Created: Read the docs
```

## How It Works

```
Command (CreateTask) → Aggregate (Task) → Event (TaskCreated)
                                              ↓
                                        EventStore.save()
                                              ↓
                                        MessageBus → Event Handlers
```

1. A **Command** expresses intent
2. The **Aggregate** validates business rules and emits **Events**
3. Events are saved to the **EventStore** (immutable audit trail)
4. Events can be published to a **MessageBus** for side-effects

## Next Steps

- [Core Concepts](concepts.md) — Aggregates, Messages, CQRS in depth
- [Demos](../demos/index.md) — Banking, E-Commerce, Lakehouse, and more
- [User Guide](../guide/index.md) — Production patterns

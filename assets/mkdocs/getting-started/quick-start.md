# Quick Start

This guide will walk you through creating your first Orchestrix application.

## Your First Module

Let's build a simple task management system using event sourcing:

### 1. Define Messages

```python
from dataclasses import dataclass
from orchestrix import Command, Event

@dataclass(frozen=True, kw_only=True)
class CreateTask(Command):
    task_id: str
    title: str
    description: str

@dataclass(frozen=True, kw_only=True)
class TaskCreated(Event):
    task_id: str
    title: str
    description: str

@dataclass(frozen=True, kw_only=True)
class CompleteTask(Command):
    task_id: str

@dataclass(frozen=True, kw_only=True)
class TaskCompleted(Event):
    task_id: str
```

### 2. Create an Aggregate

```python
from dataclasses import dataclass, field

@dataclass
class Task:
    """Task aggregate root."""
    task_id: str
    title: str
    description: str
    completed: bool = False
    _events: list[Event] = field(default_factory=list, repr=False)
    
    @classmethod
    def create(cls, task_id: str, title: str, description: str) -> "Task":
        """Create a new task."""
        task = cls(task_id=task_id, title=title, description=description)
        task._events.append(TaskCreated(
            task_id=task_id,
            title=title,
            description=description
        ))
        return task
    
    def complete(self) -> None:
        """Mark task as completed."""
        if self.completed:
            raise ValueError("Task already completed")
        self.completed = True
        self._events.append(TaskCompleted(task_id=self.task_id))
    
    def collect_events(self) -> list[Event]:
        """Collect and clear pending events."""
        events = self._events.copy()
        self._events.clear()
        return events
```

### 3. Implement Command Handlers

```python
from orchestrix import CommandHandler, MessageBus, EventStore

class CreateTaskHandler(CommandHandler[CreateTask]):
    """Handle CreateTask command."""
    
    def __init__(self, bus: MessageBus, store: EventStore) -> None:
        self.bus = bus
        self.store = store
    
    def handle(self, command: CreateTask) -> None:
        # Create aggregate
        task = Task.create(
            task_id=command.task_id,
            title=command.title,
            description=command.description
        )
        
        # Collect and publish events
        events = task.collect_events()
        self.store.save(command.task_id, events)
        for event in events:
            self.bus.publish(event)

class CompleteTaskHandler(CommandHandler[CompleteTask]):
    """Handle CompleteTask command."""
    
    def __init__(self, bus: MessageBus, store: EventStore) -> None:
        self.bus = bus
        self.store = store
    
    def handle(self, command: CompleteTask) -> None:
        # Reconstruct aggregate from events
        events = self.store.load(command.task_id)
        task = self._reconstruct_task(events)
        
        # Execute business logic
        task.complete()
        
        # Save new events
        new_events = task.collect_events()
        self.store.save(command.task_id, new_events)
        for event in new_events:
            self.bus.publish(event)
    
    def _reconstruct_task(self, events: list[Event]) -> Task:
        """Reconstruct task from event stream."""
        task = None
        for event in events:
            if isinstance(event, TaskCreated):
                task = Task(
                    task_id=event.task_id,
                    title=event.title,
                    description=event.description
                )
            elif isinstance(event, TaskCompleted):
                task.completed = True
        return task
```

### 4. Create a Module

```python
from orchestrix import Module, MessageBus, EventStore

class TaskModule(Module):
    """Task management module."""
    
    def register(self, bus: MessageBus, store: EventStore) -> None:
        """Register handlers with the bus."""
        bus.subscribe(CreateTask, CreateTaskHandler(bus, store))
        bus.subscribe(CompleteTask, CompleteTaskHandler(bus, store))
        
        # Optional: Subscribe to events for side effects
        bus.subscribe(TaskCreated, lambda event: print(f"📝 Task created: {event.title}"))
        bus.subscribe(TaskCompleted, lambda event: print(f"✅ Task completed: {event.task_id}"))
```

### 5. Wire Everything Together

```python
from orchestrix import InMemoryMessageBus, InMemoryEventStore

# Create infrastructure
bus = InMemoryMessageBus()
store = InMemoryEventStore()

# Register module
module = TaskModule()
module.register(bus, store)

# Execute commands
bus.publish(CreateTask(
    task_id="TASK-001",
    title="Learn Orchestrix",
    description="Complete the quick start guide"
))

bus.publish(CompleteTask(task_id="TASK-001"))
```

**Output:**
```
📝 Task created: Learn Orchestrix
✅ Task completed: TASK-001
```

## Next Steps

**Learn More:**

- [Core Concepts](concepts.md) - Understand Messages, Commands, and Events
- [Creating Modules](../guide/creating-modules.md) - Best practices for module design
- [Event Store Guide](../guide/event-store.md) - Persist and replay events
- [Best Practices](../guide/best-practices.md) - Production patterns

**Explore Demos:**

- [Banking Example](../demos/banking.md) - Simple event sourcing with accounts
- [E-Commerce Example](../demos/ecommerce.md) - Saga pattern for order processing  
- [Notifications Example](../demos/notifications.md) - Retry logic and error handling
- [GDPR Lakehouse](../demos/lakehouse.md) - Complete compliance example
- [All Examples](../demos/index.md) - Browse all production-ready samples

**API Reference:**

- [Core API](../api/core.md) - Commands, Events, Aggregates
- [Infrastructure API](../api/infrastructure.md) - Message Bus, Event Store

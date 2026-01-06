# Core API Reference

## Messages

### `Message`

Base class for all messages in Orchestrix.

```python
@dataclass(frozen=True, kw_only=True)
class Message:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = field(default="")
    source: str = field(default="orchestrix")
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
```

**Attributes:**

- `id` (str): Unique message identifier (UUID by default)
- `type` (str): Message type (auto-derived from class name)
- `source` (str): Message source identifier
- `timestamp` (str): ISO 8601 timestamp when message was created

**Example:**

```python
from orchestrix import Message

@dataclass(frozen=True, kw_only=True)
class UserLoggedIn(Message):
    user_id: str
    ip_address: str
```

### `Command`

Subclass of `Message` representing an intention to change state.

```python
class Command(Message):
    """A command message that represents an intention."""
    pass
```

**Usage:**

```python
from orchestrix import Command

@dataclass(frozen=True, kw_only=True)
class CreateUser(Command):
    user_id: str
    email: str
    name: str
```

### `Event`

Subclass of `Message` representing a fact that occurred.

```python
class Event(Message):
    """An event message that represents a fact."""
    pass
```

**Usage:**

```python
from orchestrix import Event

@dataclass(frozen=True, kw_only=True)
class UserCreated(Event):
    user_id: str
    email: str
    name: str
```

---

## Message Bus

### `MessageBus` (Protocol)

Protocol defining the message bus interface.

```python
class MessageBus(Protocol):
    def subscribe(self, message_type: type[Message], handler: Callable[[Message], None]) -> None:
        """Subscribe a handler to a message type."""
        ...
    
    def publish(self, message: Message) -> None:
        """Publish a message to all subscribers."""
        ...
```

**Methods:**

#### `subscribe(message_type, handler)`

Register a handler for a specific message type.

**Parameters:**

- `message_type` (type[Message]): The message class to handle
- `handler` (Callable): Function or handler instance with `handle()` method

**Example:**

```python
bus.subscribe(CreateUser, create_user_handler)
bus.subscribe(UserCreated, lambda event: print(f"User created: {event.email}"))
```

#### `publish(message)`

Publish a message to all registered handlers.

**Parameters:**

- `message` (Message): The message instance to publish

**Example:**

```python
bus.publish(CreateUser(
    user_id="USR-001",
    email="alice@example.com",
    name="Alice"
))
```

---

## Event Store

### `EventStore` (Protocol)

Protocol defining the event store interface.

```python
class EventStore(Protocol):
    def save(self, aggregate_id: str, events: list[Event]) -> None:
        """Save events for an aggregate."""
        ...
    
    def load(self, aggregate_id: str) -> list[Event]:
        """Load all events for an aggregate."""
        ...
```

**Methods:**

#### `save(aggregate_id, events)`

Persist events for an aggregate.

**Parameters:**

- `aggregate_id` (str): Unique identifier for the aggregate
- `events` (list[Event]): Events to persist

**Example:**

```python
events = [
    UserCreated(user_id="USR-001", email="alice@example.com", name="Alice"),
    UserEmailVerified(user_id="USR-001")
]
store.save("USR-001", events)
```

#### `load(aggregate_id)`

Retrieve all events for an aggregate.

**Parameters:**

- `aggregate_id` (str): Unique identifier for the aggregate

**Returns:**

- `list[Event]`: All events in chronological order

**Example:**

```python
events = store.load("USR-001")
user = reconstruct_user(events)
```

---

## Command Handler

### `CommandHandler` (Protocol)

Protocol defining command handler interface.

```python
class CommandHandler(Protocol[CommandT]):
    def handle(self, command: CommandT) -> None:
        """Handle a command."""
        ...
```

**Type Parameters:**

- `CommandT`: The specific command type this handler processes

**Example:**

```python
from orchestrix import CommandHandler, Command, MessageBus, EventStore

class CreateUserHandler(CommandHandler[CreateUser]):
    def __init__(self, bus: MessageBus, store: EventStore) -> None:
        self.bus = bus
        self.store = store
    
    def handle(self, command: CreateUser) -> None:
        # Create user aggregate
        user = User.create(command.user_id, command.email, command.name)
        
        # Save and publish events
        events = user.collect_events()
        self.store.save(command.user_id, events)
        for event in events:
            self.bus.publish(event)
```

---

## Module

### `Module` (Protocol)

Protocol defining module interface.

```python
class Module(Protocol):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        """Register the module's handlers with the bus and store."""
        ...
```

**Methods:**

#### `register(bus, store)`

Wire up module handlers with infrastructure.

**Parameters:**

- `bus` (MessageBus): Message bus instance
- `store` (EventStore): Event store instance

**Example:**

```python
from orchestrix import Module, MessageBus, EventStore

class UserModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        # Register command handlers
        bus.subscribe(CreateUser, CreateUserHandler(bus, store))
        bus.subscribe(VerifyUserEmail, VerifyUserEmailHandler(bus, store))
        
        # Register event handlers
        bus.subscribe(UserCreated, send_welcome_email)
        bus.subscribe(UserEmailVerified, log_verification)
```

---

## Complete Example

```python
from dataclasses import dataclass, field
from orchestrix import (
    Command, Event, CommandHandler, Module,
    MessageBus, EventStore,
    InMemoryMessageBus, InMemoryEventStore
)

# Messages
@dataclass(frozen=True, kw_only=True)
class RegisterUser(Command):
    user_id: str
    email: str

@dataclass(frozen=True, kw_only=True)
class UserRegistered(Event):
    user_id: str
    email: str

# Aggregate
@dataclass
class User:
    user_id: str
    email: str
    _events: list[Event] = field(default_factory=list, repr=False)
    
    @classmethod
    def register(cls, user_id: str, email: str):
        user = cls(user_id, email)
        user._events.append(UserRegistered(user_id=user_id, email=email))
        return user
    
    def collect_events(self) -> list[Event]:
        events = self._events.copy()
        self._events.clear()
        return events

# Handler
class RegisterUserHandler(CommandHandler[RegisterUser]):
    def __init__(self, bus: MessageBus, store: EventStore) -> None:
        self.bus = bus
        self.store = store
    
    def handle(self, command: RegisterUser) -> None:
        user = User.register(command.user_id, command.email)
        events = user.collect_events()
        self.store.save(command.user_id, events)
        for event in events:
            self.bus.publish(event)

# Module
class UserModule(Module):
    def register(self, bus: MessageBus, store: EventStore) -> None:
        bus.subscribe(RegisterUser, RegisterUserHandler(bus, store))

# Application
bus = InMemoryMessageBus()
store = InMemoryEventStore()
UserModule().register(bus, store)

bus.publish(RegisterUser(user_id="USR-001", email="alice@example.com"))
```

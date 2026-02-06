"""Demo bootstrap – initialise InMemory EventStore, MessageBus and background command sender."""

from orchestrix.core.messaging.message import Command, Event
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus
from orchestrix.infrastructure.memory.store import InMemoryEventStore


class DemoCommandHandler:
    """Simple handler that turns commands into events with 20 % random failure."""

    def __init__(
        self,
        bus: InMemoryMessageBus,
        store: InMemoryEventStore,
        flow_state: dict,
    ) -> None:
        """Initialise handler with bus, store and shared flow state."""
        self.bus = bus
        self.store = store
        self._state = flow_state

    def handle(self, command: Command) -> None:
        """Process a command, generating events or recording errors."""
        import random
        import time
        from uuid import uuid4

        trace_id = getattr(command, "trace_id", None)
        if not trace_id:
            trace_id = str(uuid4())
            object.__setattr__(command, "trace_id", trace_id)

        if random.random() < 0.2:
            error = f"Simulated error for command {command.type}"
            self._state["errors"].append(
                {
                    "timestamp": time.time(),
                    "command": str(command),
                    "error": error,
                    "trace_id": trace_id,
                }
            )
            self._state["history"].append(
                {
                    "step": "error",
                    "type": command.type,
                    "id": getattr(command, "id", None),
                    "timestamp": time.time(),
                    "status": "error",
                    "error": error,
                    "trace_id": trace_id,
                }
            )
            return

        if command.type == "CreateOrder":
            event = Event(type="OrderCreated", data=command.data, trace_id=trace_id)
            self.store.save(command.data["order_id"], [event])
            self.bus.publish(event)
        elif command.type == "CancelOrder":
            event = Event(type="OrderCancelled", data=command.data, trace_id=trace_id)
            self.store.save(command.data["order_id"], [event])
            self.bus.publish(event)


def bootstrap_demo() -> tuple:
    """Bootstrap the demo with in-memory event store, bus and background sender."""
    import random
    import string
    import threading
    import time

    event_store = InMemoryEventStore()
    bus = InMemoryMessageBus()

    # ── Flow tracing state (shared mutable dict) ────────────────
    flow_tracing_state = {
        "active_commands": [],
        "active_events": [],
        "history": [],
        "errors": [],
    }

    def trace_command(command: Command) -> None:
        """Record an incoming command in the flow tracing state."""
        entry = {
            "id": getattr(command, "id", None),
            "type": getattr(command, "type", str(command)),
            "payload": getattr(command, "data", {}),
            "timestamp": time.time(),
            "status": "received",
            "trace_id": getattr(command, "trace_id", None),
        }
        flow_tracing_state["active_commands"].append(entry)
        flow_tracing_state["history"].append({"step": "command", **entry})

    def trace_event(event: Event, caused_by: dict | None = None) -> None:
        """Record an emitted event in the flow tracing state."""
        static_trace_id = None
        if caused_by and isinstance(caused_by, dict):
            static_trace_id = caused_by.get("id")
        entry = {
            "id": getattr(event, "id", None),
            "type": getattr(event, "type", str(event)),
            "payload": getattr(event, "data", {}),
            "timestamp": time.time(),
            "status": "emitted",
            "caused_by": caused_by,
            "trace_id": static_trace_id or getattr(event, "trace_id", None),
        }
        flow_tracing_state["active_events"].append(entry)
        flow_tracing_state["history"].append({"step": "event", **entry})

    handler = DemoCommandHandler(bus, event_store, flow_tracing_state)
    bus.subscribe(Command, handler.handle)
    bus.subscribe(Event, trace_event)

    def random_order_id() -> str:
        return "ORD-" + "".join(random.choices(string.digits, k=3))

    def random_command() -> Command:
        cmd_type = random.choice(["CreateOrder", "CancelOrder"])
        if cmd_type == "CreateOrder":
            data = {
                "order_id": random_order_id(),
                "customer_name": random.choice(["Alice", "Bob", "Charlie", "Demo"]),
                "total_amount": round(random.uniform(10, 100), 2),
            }
        else:
            # Cancel a random order (simulate existing ones)
            data = {"order_id": random_order_id()}
        return Command(type=cmd_type, data=data)

    def command_sender() -> None:
        while True:
            cmd = random_command()
            trace_command(cmd)
            bus.publish(cmd)
            time.sleep(2)

    # Start background thread for random commands
    thread = threading.Thread(target=command_sender, daemon=True)
    thread.start()

    # Export tracing functions for GUI
    return event_store, None, bus, flow_tracing_state, trace_command, trace_event

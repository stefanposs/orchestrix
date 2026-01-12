"""
Demo-Bootstrap: Initialisiert InMemory-EventStore, MessageBus, registriert Events, Aggregate, Module und führt einen Beispielprozess aus.
"""

# Orchestrix-Framework-Importe
from orchestrix.infrastructure.memory.store import InMemoryEventStore
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus
from orchestrix.core.messaging.message import Command, Event
# Aggregate, CommandHandler etc. können je nach Domain/Beispiel importiert werden

# Dummy-CommandHandler für Demo (ersetzt durch echte Domain-Handler im Produktivcode)
class DemoCommandHandler:
    def __init__(self, bus, store):
        self.bus = bus
        self.store = store
    def handle(self, command: Command):
        import random
        import time
        from uuid import uuid4
        # Simpler Demo-Handler: Command -> Event, with random error simulation
        error = None
        # trace_id generieren, falls nicht vorhanden
        trace_id = getattr(command, "trace_id", None)
        if not trace_id:
            trace_id = str(uuid4())
            object.__setattr__(command, "trace_id", trace_id)
        if random.random() < 0.2:  # 20% chance of error
            error = f"Simulated error for command {command.type}"
            flow_tracing_state["errors"].append({
                "timestamp": time.time(),
                "command": str(command),
                "error": error,
                "trace_id": trace_id
            })
            flow_tracing_state["history"].append({
                "step": "error", "type": command.type, "id": getattr(command, "id", None), "timestamp": time.time(), "status": "error", "error": error, "trace_id": trace_id
            })
            return
        if command.type == "CreateOrder":
            event = Event(type="OrderCreated", data=command.data, trace_id=trace_id)
            self.store.save(command.data["order_id"], [event])
            self.bus.publish(event)
        elif command.type == "CancelOrder":
            event = Event(type="OrderCancelled", data=command.data, trace_id=trace_id)
            self.store.save(command.data["order_id"], [event])
            self.bus.publish(event)

def bootstrap_demo():
    event_store = InMemoryEventStore()
    bus = InMemoryMessageBus()

    def trace_command(command):
        entry = {
            "id": getattr(command, "id", None),
            "type": getattr(command, "type", str(command)),
            "payload": getattr(command, "data", {}),
            "timestamp": time.time(),
            "status": "received",
            "trace_id": getattr(command, "trace_id", None)
        }
        flow_tracing_state["active_commands"].append(entry)
        flow_tracing_state["history"].append({"step": "command", **entry})

    def trace_event(event, caused_by=None):
        # Use command guid/id as static trace_id if available
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
            "trace_id": static_trace_id or getattr(event, "trace_id", None)
        }
        flow_tracing_state["active_events"].append(entry)
        flow_tracing_state["history"].append({"step": "event", **entry})

    handler = DemoCommandHandler(bus, event_store)
    bus.subscribe(Command, handler.handle)
    bus.subscribe(Event, trace_event)

    # FLOW TRACING STATE
    import time
    global flow_tracing_state
    flow_tracing_state = {
        "active_commands": [],  # List of dicts: {id, type, payload, timestamp, status}
        "active_events": [],    # List of dicts: {id, type, payload, timestamp, status, caused_by}
        "history": [],          # List of dicts: {step, type, id, timestamp, status, caused_by, error}
        "errors": []            # List of dicts: {timestamp, command, error}
    }

    def trace_command(command):
        entry = {
            "id": getattr(command, "id", None),
            "type": getattr(command, "type", str(command)),
            "payload": getattr(command, "data", {}),
            "timestamp": time.time(),
            "status": "received",
            "trace_id": getattr(command, "trace_id", None)
        }
        flow_tracing_state["active_commands"].append(entry)
        flow_tracing_state["history"].append({"step": "command", **entry})

    def trace_event(event, caused_by=None):
        # Use command guid/id as static trace_id if available
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
            "trace_id": static_trace_id or getattr(event, "trace_id", None)
        }
        flow_tracing_state["active_events"].append(entry)
        flow_tracing_state["history"].append({"step": "event", **entry})

    import threading, random, string
    def random_order_id():
        return "ORD-" + ''.join(random.choices(string.digits, k=3))

    def random_command():
        cmd_type = random.choice(["CreateOrder", "CancelOrder"])
        if cmd_type == "CreateOrder":
            data = {
                "order_id": random_order_id(),
                "customer_name": random.choice(["Alice", "Bob", "Charlie", "Demo"]),
                "total_amount": round(random.uniform(10, 100), 2)
            }
        else:
            # Cancel a random order (simulate existing ones)
            data = {"order_id": random_order_id()}
        return Command(type=cmd_type, data=data)

    def command_sender():
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

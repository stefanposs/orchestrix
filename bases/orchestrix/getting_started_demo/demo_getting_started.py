"""Getting Started Demo for orchestrix.

-----------------------------------
Dieses Beispiel zeigt, wie man ein Event und einen Handler registriert und ausführt.
"""

from dataclasses import dataclass
from orchestrix.core.messaging import Event
from orchestrix.infrastructure.memory import InMemoryMessageBus


@dataclass(frozen=True, kw_only=True)
class HelloWorld(Event):
    """Event representing a hello world message.

    Attributes:
    ----------
    message : str
        The message to be sent with the event.
    """

    message: str


def handle_hello(event: HelloWorld):
    """Handle the HelloWorld event by printing its message.

    Parameters:
    ----------
    event : HelloWorld
        The event containing the message to be printed.
    """
    print(f"Received: {event.message}")


bus = InMemoryMessageBus()
bus.subscribe(HelloWorld, handle_hello)
bus.publish(HelloWorld(message="Willkommen bei orchestrix!"))

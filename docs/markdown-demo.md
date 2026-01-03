# Markdown Demo

## Code Blocks mit Syntax Highlighting

```python
from orchestrix import Command, Event

@dataclass(frozen=True, kw_only=True)
class CreateUser(Command):
    user_id: str
    email: str
```

## Admonitions (Info-Boxen)

!!! note "Hinweis"
    Dies ist eine Info-Box für zusätzliche Informationen.

!!! tip "Tipp"
    Nutze `just docs` um die Dokumentation zu starten!

!!! warning "Warnung"
    Achte darauf, dass alle Commands immutable sind.

!!! danger "Achtung"
    Event Store kann nicht rückwärts laufen!

## Tabs

=== "Python"
    ```python
    bus = InMemoryMessageBus()
    ```

=== "JavaScript"
    ```javascript
    const bus = new InMemoryMessageBus();
    ```

=== "TypeScript"
    ```typescript
    const bus: MessageBus = new InMemoryMessageBus();
    ```

## Tabellen

| Feature | Status | Beschreibung |
|---------|--------|--------------|
| Commands | ✅ | Implementiert |
| Events | ✅ | Implementiert |
| Async Bus | ⏳ | Geplant |
| Postgres Store | ⏳ | Geplant |

## Task Lists

- [x] Core Framework implementieren
- [x] InMemory Infrastructure
- [x] Tests mit 100% Coverage
- [ ] Async MessageBus
- [ ] PostgreSQL EventStore
- [ ] Redis MessageBus

## Footnotes

Orchestrix nutzt CloudEvents[^1] für Message-Kompatibilität.

[^1]: [CloudEvents Specification](https://cloudevents.io)

## Emojis

🎯 Modular Design  
📦 Event Sourcing  
☁️ CloudEvents Compatible  
🔌 Pluggable Infrastructure  
🧪 Type-Safe  
🚀 Simple API

# Distributed Tracing with OpenTelemetry

Distributed tracing provides end-to-end visibility into message flows across services.

## Overview

Orchestrix integrates with OpenTelemetry to automatically create spans for command/event handling, providing distributed tracing across your event-driven architecture.

## Key Features

- **Automatic Instrumentation** - Traces all message handling
- **Context Propagation** - Via CloudEvents metadata
- **Jaeger Integration** - Export to Jaeger for visualization
- **Production Ready** - Low overhead, high throughput

## Basic Example

```python
from orchestrix.infrastructure.tracing import init_tracing, TraceConfig
from orchestrix.infrastructure import InMemoryMessageBus
from orchestrix.core.messaging.message import Command, Event
from dataclasses import dataclass

# Initialize tracing
init_tracing(
    TraceConfig(
        service_name="order-service",
        jaeger_endpoint="http://localhost:14268/api/traces",
        environment="production"
    )
)

@dataclass(frozen=True)
class CreateOrder(Command):
    order_id: str
    customer_name: str

@dataclass(frozen=True)
class OrderCreated(Event):
    order_id: str
    customer_name: str

# Setup
bus = InMemoryMessageBus()

def handle_create_order(cmd: CreateOrder):
    # This will be traced automatically
    print(f"Creating order {cmd.order_id}")
    bus.publish(OrderCreated(
        order_id=cmd.order_id,
        customer_name=cmd.customer_name
    ))

def handle_order_created(event: OrderCreated):
    # This will also be traced
    print(f"Order created: {event.order_id}")

bus.subscribe(CreateOrder, handle_create_order)
bus.subscribe(OrderCreated, handle_order_created)

# Publish command - generates trace
bus.publish(CreateOrder(
    order_id="ORD-001",
    customer_name="Alice"
))
```

## Running with Jaeger

### Start Jaeger

```bash
docker run -d --name jaeger \
  -p 6831:6831/udp \
  -p 16686:16686 \
  -p 14268:14268 \
  jaegertracing/all-in-one:latest
```

### Run Example

```bash
cd examples/tracing
uv run example.py
```

### View Traces

Open [http://localhost:16686](http://localhost:16686) in your browser.

## Trace Context Propagation

Traces automatically propagate across service boundaries via CloudEvents:

```python
# Service A
event = OrderCreated(
    order_id="ORD-001",
    customer_name="Alice"
)
# Trace context added to CloudEvents metadata
bus.publish(event)

# Service B receives event with trace context
# Continues the same trace automatically
```

## Custom Spans

Add custom spans for detailed tracking:

```python
from orchestrix.infrastructure.tracing import create_span

async def handle_order(cmd: CreateOrder):
    with create_span("validate-order") as span:
        span.set_attribute("order_id", cmd.order_id)
        # Validation logic
        
    with create_span("save-order") as span:
        # Persistence logic
        pass
```

## Configuration

```python
TraceConfig(
    service_name="order-service",          # Service identifier
    jaeger_endpoint="http://localhost:14268/api/traces",
    environment="production",              # Environment tag
    sample_rate=1.0,                       # Sample 100% of traces
    max_tag_length=1024                    # Max attribute length
)
```

## Best Practices

1. **Service Names** - Use descriptive, unique names
2. **Sampling** - Reduce sample_rate in high-volume production
3. **Attributes** - Add relevant context to spans
4. **Error Handling** - Traces capture exceptions automatically

## Metrics Available

- Request duration (p50, p95, p99)
- Error rates
- Service dependencies
- Call graphs

## Learn More

- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [Full Example](https://github.com/stefanposs/orchestrix/tree/main/examples/tracing)
- [API Reference](../api/infrastructure.md#tracing)

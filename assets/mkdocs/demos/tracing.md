
# Tracing — Distributed Observability

Orchestrix includes built-in tracing support via OpenTelemetry and Jaeger.

## Infrastructure

Tracing is provided by the `infrastructure/observability` package:

```python
from orchestrix.infrastructure.observability import JaegerTracer, TracingConfig

# Initialize
config = TracingConfig(service_name="my-service", jaeger_agent_host="localhost")
tracer = JaegerTracer()

# Trace a command
with tracer.span_command("CreateOrder", aggregate_id="order-123"):
    # ... handle command ...
    pass

# Trace an event
with tracer.span_event("OrderCreated", event_id="evt-1", aggregate_id="order-123"):
    # ... process event ...
    pass

# Trace a saga
with tracer.span_saga("OrderSaga", saga_id="saga-1"):
    # ... execute saga steps ...
    pass
```

## Async Support

```python
async with tracer.async_span_command("ProcessPayment", aggregate_id="order-123"):
    await process_payment(...)
```

## Trace Context

```python
trace_id = tracer.get_trace_id()
tracer.set_attribute("customer_id", "cust-456")
tracer.add_event("payment_authorized", {"amount": "99.99"})
```

## Prerequisites

```bash
uv add orchestrix[observability]
# Requires: opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp
```

## Related

- [Prometheus Metrics](../guide/production-ready.md) — Monitoring setup
- [Production Deployment](../guide/production-deployment.md) — Infrastructure guidance

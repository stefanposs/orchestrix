
# Production Deployment

Infrastructure guidance for deploying Orchestrix at different scales.

## Architecture Overview

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   FastAPI /   │────▶│  MessageBus  │────▶│  Event Handlers  │
│   Client App  │     │  (Pub/Sub)   │     │  (projections,   │
└──────────────┘     └──────┬───────┘     │   notifications) │
                            │              └──────────────────┘
                     ┌──────▼───────┐
                     │  EventStore  │
                     │  (Postgres)  │
                     └──────────────┘
```

## Small Projects (< 10k events/month)

```python
from orchestrix.infrastructure.memory.store import InMemoryEventStore
from orchestrix.infrastructure.memory.bus import InMemoryMessageBus

store = InMemoryEventStore()
bus = InMemoryMessageBus()
```

- Single process, in-memory store
- Suitable for prototypes, demos, small internal tools
- No external dependencies

## Medium Projects (10k–100k events/month)

```python
from orchestrix.infrastructure.postgres.store import PostgreSQLEventStore

store = PostgreSQLEventStore(
    connection_string="postgresql://user:pw@localhost:5432/orchestrix",
    pool_min_size=5,
    pool_max_size=20,
)
await store.initialize()
```

- PostgreSQL for persistence
- Single application server
- Add observability:

```python
from orchestrix.infrastructure.observability import PrometheusMetrics, MetricConfig

metrics = PrometheusMetrics(MetricConfig(namespace="myapp"))

with metrics.track_event_publish(event_type="OrderCreated"):
    store.save(aggregate_id, events)
```

## Large Projects (> 100k events/month)

- **PostgreSQL** with connection pooling (PgBouncer)
- **GCP Pub/Sub** for distributed message bus
- **Jaeger** for distributed tracing
- **Prometheus** for metrics
- Horizontal scaling with multiple application instances

```python
from orchestrix.infrastructure.gcp_pubsub import GCPPubSub
from orchestrix.infrastructure.observability import JaegerTracer, TracingConfig

bus = GCPPubSub(project_id="prod", topic_id="orchestrix-events")
tracer = JaegerTracer()

async with tracer.async_span("process_order"):
    await bus.publish(OrderCreated(...))
```

## Docker Deployment

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync --frozen
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "bases.orchestrix.lakehouse_fastapi_demo.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Configuration Checklist

| Setting | Dev | Staging | Production |
|---|---|---|---|
| Event Store | InMemory | PostgreSQL | PostgreSQL + PgBouncer |
| Message Bus | InMemory | InMemory | GCP Pub/Sub |
| Tracing | Off | Jaeger | Jaeger |
| Metrics | Off | Prometheus | Prometheus + Grafana |
| Log Level | DEBUG | INFO | WARNING |
| Pool Size | 2 | 10 | 50 |

## Health Checks

The Lakehouse demo includes built-in probes:

```yaml
# Kubernetes
livenessProbe:
  httpGet:
    path: /health
    port: 8000
readinessProbe:
  httpGet:
    path: /ready
    port: 8000
```

## Migration Strategy

1. Start with `InMemoryEventStore` for development
2. Switch to `PostgreSQLEventStore` for staging/production
3. Add `PrometheusMetrics` for observability
4. Add `JaegerTracer` for distributed tracing
5. Move to `GCPPubSub` when you need multi-instance messaging

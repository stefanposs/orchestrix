
# Production Readiness Checklist

Use this checklist before launching to production.

## Data Persistence

- [ ] Using `PostgreSQLEventStore` (not `InMemoryEventStore`)
- [ ] Connection pooling configured (`pool_min_size`, `pool_max_size`)
- [ ] Database backups automated
- [ ] `expected_version` used for optimistic concurrency
- [ ] Snapshot strategy defined for high-event aggregates

## Observability

### Metrics (Prometheus)

```python
from orchestrix.infrastructure.observability import PrometheusMetrics, MetricConfig

metrics = PrometheusMetrics(MetricConfig(namespace="myapp"))
```

Built-in metrics tracked:

| Metric | Type | Description |
|---|---|---|
| `events_total` | Counter | Events published |
| `events_processing_seconds` | Histogram | Event processing duration |
| `commands_total` | Counter | Commands handled |
| `commands_latency_seconds` | Histogram | Command handling duration |
| `aggregates_loaded_total` | Counter | Aggregates loaded |
| `saga_executions_total` | Counter | Saga executions |
| `saga_duration_seconds` | Histogram | Saga execution time |

### Tracing (OpenTelemetry / Jaeger)

```python
from orchestrix.infrastructure.observability import JaegerTracer, TracingConfig

config = TracingConfig(service_name="my-service", jaeger_agent_host="jaeger")
tracer = JaegerTracer()
```

### Logging

```python
from orchestrix.core.common.logging import StructuredLogger, get_logger

logger = StructuredLogger(get_logger("myapp"))
logger.info("order_created", order_id="123", amount=99.0)
```

## Error Handling

- [ ] `HandlerError` caught and logged
- [ ] `ConcurrencyError` handled with retry
- [ ] Dead letter queue for failed messages
- [ ] Retry policies configured:

```python
from orchestrix.core.common.retry import ExponentialBackoff

policy = ExponentialBackoff(max_retries=3, initial_delay=1.0, multiplier=2.0)
```

## Security

- [ ] Input validation on all commands (`validate_not_empty`, etc.)
- [ ] Log sanitization (no user data in plain logs)
- [ ] Database credentials in environment variables
- [ ] HTTPS enabled

## Testing

- [ ] Unit tests for aggregates (business rules)
- [ ] Integration tests with `InMemoryEventStore`
- [ ] Saga compensation tested
- [ ] Event replay tested

```bash
# Run full QA
just qa          # lint + format + type check + tests
just test        # tests only
just lint        # ruff check
just ty          # type checking
```

## Performance

- [ ] Snapshot interval set for high-event aggregates
- [ ] Connection pool sized for expected load
- [ ] Event store indexed (handled by `PostgreSQLEventStore.initialize()`)
- [ ] Async handlers for I/O operations

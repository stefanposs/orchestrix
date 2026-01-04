# Prometheus Metrics

Production-grade metrics collection for monitoring and alerting.

## Overview

Orchestrix automatically collects metrics for message throughput, handler latency, event store performance, and more using Prometheus.

## Key Features

- **Automatic Collection** - No manual instrumentation needed
- **Rich Metrics** - Throughput, latency, errors, event store ops
- **Standard Format** - Prometheus-compatible format
- **Low Overhead** - Minimal performance impact

## Basic Example

```python
from orchestrix.infrastructure.prometheus_metrics import init_metrics, MetricsConfig
from orchestrix.infrastructure import InMemoryMessageBus
from orchestrix.core.message import Command, Event
from dataclasses import dataclass
import time

# Initialize metrics
init_metrics(
    MetricsConfig(
        port=8000,
        path="/metrics",
        enable_default_metrics=True
    )
)

@dataclass(frozen=True)
class ProcessOrder(Command):
    order_id: str

@dataclass(frozen=True)
class OrderProcessed(Event):
    order_id: str

# Setup
bus = InMemoryMessageBus()

def handle_process_order(cmd: ProcessOrder):
    # Simulate work
    time.sleep(0.1)
    bus.publish(OrderProcessed(order_id=cmd.order_id))

def handle_order_processed(event: OrderProcessed):
    print(f"Order processed: {event.order_id}")

bus.subscribe(ProcessOrder, handle_process_order)
bus.subscribe(OrderProcessed, handle_order_processed)

# Process orders - metrics collected automatically
for i in range(100):
    bus.publish(ProcessOrder(order_id=f"ORD-{i:03d}"))
```

## Running the Example

```bash
cd examples/prometheus
uv run example.py
```

Open [http://localhost:8000/metrics](http://localhost:8000/metrics) to view metrics.

## Available Metrics

### Message Throughput

```
# HELP orchestrix_messages_total Total messages published
# TYPE orchestrix_messages_total counter
orchestrix_messages_total{type="command",name="ProcessOrder"} 100
orchestrix_messages_total{type="event",name="OrderProcessed"} 100

# HELP orchestrix_messages_per_second Messages published per second
# TYPE orchestrix_messages_per_second gauge
orchestrix_messages_per_second 45.2
```

### Handler Latency

```
# HELP orchestrix_handler_duration_seconds Handler execution time
# TYPE orchestrix_handler_duration_seconds histogram
orchestrix_handler_duration_seconds_bucket{handler="handle_process_order",le="0.1"} 95
orchestrix_handler_duration_seconds_bucket{handler="handle_process_order",le="0.5"} 100
orchestrix_handler_duration_seconds_sum{handler="handle_process_order"} 10.234
orchestrix_handler_duration_seconds_count{handler="handle_process_order"} 100
```

### Event Store Performance

```
# HELP orchestrix_store_operations_total Event store operations
# TYPE orchestrix_store_operations_total counter
orchestrix_store_operations_total{operation="save",store="postgres"} 1000
orchestrix_store_operations_total{operation="load",store="postgres"} 500

# HELP orchestrix_store_duration_seconds Event store operation duration
# TYPE orchestrix_store_duration_seconds histogram
orchestrix_store_duration_seconds_sum{operation="save"} 5.432
orchestrix_store_duration_seconds_count{operation="save"} 1000
```

### Error Rates

```
# HELP orchestrix_errors_total Total errors
# TYPE orchestrix_errors_total counter
orchestrix_errors_total{type="handler_error",handler="handle_order"} 3
orchestrix_errors_total{type="concurrency_error",aggregate="order"} 2
```

## Grafana Dashboard

Import the included Grafana dashboard for visualization:

```bash
# Located at: examples/prometheus/grafana_dashboard.json
```

Dashboard includes:
- Message throughput over time
- Handler latency percentiles (p50, p95, p99)
- Error rates by type
- Event store performance
- Active handlers

## Alerting Rules

Example Prometheus alerting rules:

```yaml
groups:
  - name: orchestrix
    rules:
      - alert: HighErrorRate
        expr: rate(orchestrix_errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
      
      - alert: SlowHandlers
        expr: histogram_quantile(0.95, orchestrix_handler_duration_seconds) > 1.0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Handler latency p95 > 1s"
```

## Configuration

```python
MetricsConfig(
    port=8000,                          # Metrics endpoint port
    path="/metrics",                    # Metrics path
    enable_default_metrics=True,        # Include Python runtime metrics
    histogram_buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0]  # Latency buckets
)
```

## Best Practices

1. **Labels** - Use cardinality-limited labels (avoid unique IDs)
2. **Histograms** - Choose appropriate buckets for latency
3. **Alerts** - Set up alerting for critical metrics
4. **Dashboards** - Create service-specific dashboards

## Integration

### Docker Compose

```yaml
services:
  orchestrix-app:
    build: .
    ports:
      - "8000:8000"  # Metrics endpoint
  
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

### Prometheus Config

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'orchestrix'
    static_configs:
      - targets: ['orchestrix-app:8000']
    scrape_interval: 5s
```

## Learn More

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [Full Example](https://github.com/stefanposs/orchestrix/tree/main/examples/prometheus)
- [API Reference](../api/infrastructure.md#prometheus-metrics)

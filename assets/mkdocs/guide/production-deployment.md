# Production Deployment Guide

Complete guide for deploying Orchestrix applications from development to large-scale production.

## Overview

This guide helps you choose the right deployment architecture based on your project scale, event volume, and operational requirements.

## 📊 Project Scale Definitions

| Scale | Event Volume | Concurrent Users | Infrastructure | Team Size | 
|-------|-------------|------------------|----------------|-----------|
| **Small** | < 10k events/month | < 100 | Minimal | 1-3 developers |
| **Medium** | 10k-100k events/month | 100-1,000 | Standard | 3-10 developers |
| **Large** | > 100k events/month | 1,000+ | Enterprise | 10+ developers |

---

## 🚀 Small Projects

**Perfect for:**
- MVPs and prototypes
- Internal tools
- Startups validating product-market fit
- Development and testing

### Infrastructure

```python
from orchestrix.infrastructure import (
    InMemoryMessageBus,
    InMemoryEventStore
)

# Simple setup - no external dependencies
bus = InMemoryMessageBus()
store = InMemoryEventStore()
```

### Deployment

**Option 1: Single Process (Simplest)**

```bash
# Single gunicorn/uvicorn worker
gunicorn app:app --workers 1 --bind 0.0.0.0:8000
```

**Option 2: Docker Container**

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install orchestrix

CMD ["python", "main.py"]
```

```bash
docker build -t myapp .
docker run -p 8000:8000 myapp
```

### Limitations

⚠️ **Important Constraints:**
- Events stored in memory (lost on restart)
- Single process only (no horizontal scaling)
- No persistence (use PostgreSQL for production)
- Limited to server memory

### When to Upgrade

Move to Medium when:
- Event volume exceeds 10k/month
- Need persistence across restarts
- Multiple users accessing concurrently
- Audit trail required for compliance

---

## 📈 Medium Projects

**Perfect for:**
- Production SaaS applications
- B2B platforms
- E-commerce sites
- Financial applications

### Infrastructure

```python
from orchestrix.infrastructure import (
    InMemoryMessageBus,
    PostgresEventStore,
    ConnectionPool
)
from orchestrix.core import AggregateRepository

# PostgreSQL for persistence
pool = ConnectionPool(
    host="localhost",
    port=5432,
    database="myapp",
    user="myapp",
    password="secure_password",
    min_size=5,
    max_size=20
)

# In-memory bus for simplicity
bus = InMemoryMessageBus()

# PostgreSQL store for persistence
store = PostgresEventStore(pool)

# Aggregate repository with snapshots
repository = AggregateRepository(
    store=store,
    snapshot_frequency=50  # Snapshot every 50 events
)
```

### Database Setup

**1. Create PostgreSQL Database**

```bash
# Create database
createdb myapp

# Or via Docker
docker run -d \
  --name myapp-postgres \
  -e POSTGRES_DB=myapp \
  -e POSTGRES_USER=myapp \
  -e POSTGRES_PASSWORD=secure_password \
  -p 5432:5432 \
  postgres:16
```

**2. Run Migrations**

```sql
-- migrations/001_create_events_table.sql
CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    aggregate_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    event_data JSONB NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    version INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (aggregate_id, version)
);

CREATE INDEX idx_events_aggregate_id ON events(aggregate_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_timestamp ON events(timestamp);

-- Snapshots table (optional, for performance)
CREATE TABLE IF NOT EXISTS snapshots (
    aggregate_id VARCHAR(255) PRIMARY KEY,
    aggregate_type VARCHAR(255) NOT NULL,
    snapshot_data JSONB NOT NULL,
    version INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Deployment

**Docker Compose**

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: myapp
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myapp"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    environment:
      DATABASE_URL: postgresql://myapp:${DB_PASSWORD}@postgres:5432/myapp
      WORKERS: 4
    depends_on:
      postgres:
        condition: service_healthy
    ports:
      - "8000:8000"
    restart: unless-stopped

volumes:
  postgres_data:
```

**Kubernetes Deployment**

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: myapp:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: database-url
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Observability

**Basic Monitoring**

```python
from orchestrix.infrastructure import PrometheusMetrics

# Enable Prometheus metrics
metrics = PrometheusMetrics()
bus.add_observability_hook(metrics)
store.add_observability_hook(metrics)

# Expose metrics endpoint
from prometheus_client import make_asgi_app

# In your FastAPI/Starlette app
app.mount("/metrics", make_asgi_app())
```

**Health Checks**

```python
from fastapi import FastAPI, Response

app = FastAPI()

@app.get("/health")
async def health():
    """Liveness probe."""
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    """Readiness probe - check database."""
    try:
        # Simple query to verify DB connection
        await pool.execute("SELECT 1")
        return {"status": "ready"}
    except Exception as e:
        return Response(
            content={"status": "not ready", "error": str(e)},
            status_code=503
        )
```

### Performance Tuning

**Connection Pooling**

```python
# Tune pool size based on workload
pool = ConnectionPool(
    host="localhost",
    port=5432,
    database="myapp",
    user="myapp",
    password="secure_password",
    min_size=5,      # Keep 5 connections ready
    max_size=20,     # Allow up to 20 connections
    timeout=30,      # Connection timeout
    max_queries=1000 # Recycle connection after 1k queries
)
```

**Snapshots**

```python
# Enable snapshots for aggregates with many events
from orchestrix.core import SnapshotStrategy

repository = AggregateRepository(
    store=store,
    snapshot_frequency=50  # Snapshot every 50 events
)

# Manual snapshot
await repository.save_snapshot(aggregate_id, aggregate)

# Load with snapshot
aggregate = await repository.load(aggregate_id, Order)
```

**Batch Processing**

```python
# Process events in batches
from orchestrix.core import ProjectionEngine

engine = ProjectionEngine(
    store=store,
    batch_size=100  # Process 100 events at a time
)

# Run projection
await engine.run(OrderSummaryProjection())
```

### When to Upgrade

Move to Large when:
- Event volume exceeds 100k/month
- Need multi-region deployment
- Require advanced observability
- Team size grows beyond 10 developers
- Compliance requires enhanced audit trails

---

## 🏢 Large Projects

**Perfect for:**
- Enterprise applications
- Multi-tenant SaaS platforms
- High-traffic e-commerce
- Financial institutions
- Healthcare systems

### Infrastructure

```python
from orchestrix.infrastructure import (
    AsyncInMemoryMessageBus,
    EventSourcingDBStore,  # Or PostgreSQL cluster
    ConnectionPool,
    OpenTelemetryTracing,
    PrometheusMetrics
)
from orchestrix.core import (
    AggregateRepository,
    ProjectionEngine,
    DeadLetterQueue,
    RetryPolicy
)

# Full observability stack
tracing = OpenTelemetryTracing(
    service_name="myapp",
    jaeger_endpoint="http://jaeger:14268/api/traces"
)
metrics = PrometheusMetrics(namespace="myapp")

# Async bus for high throughput
bus = AsyncInMemoryMessageBus()
bus.add_observability_hook(tracing)
bus.add_observability_hook(metrics)

# EventSourcingDB or PostgreSQL cluster
store = EventSourcingDBStore(
    endpoint="https://eventsourcingdb.example.com",
    api_key="your-api-key"
)
store.add_observability_hook(tracing)
store.add_observability_hook(metrics)

# Dead letter queue for failed messages
dlq = DeadLetterQueue(
    store=store,
    max_retries=3,
    backoff_strategy="exponential"
)

# Repository with advanced features
repository = AggregateRepository(
    store=store,
    snapshot_frequency=50,
    cache_ttl=300,  # 5-minute cache
    optimistic_locking=True
)
```

### Database Setup

**Option 1: EventSourcingDB (Recommended)**

```bash
# Docker deployment
docker run -d \
  --name eventsourcingdb \
  -p 2113:2113 \
  -e EVENTSOURCINGDB_LICENSE_KEY=${LICENSE_KEY} \
  eventsourcingdb/eventsourcingdb:latest

# Kubernetes with Helm
helm repo add eventsourcingdb https://charts.eventsourcingdb.com
helm install myapp-events eventsourcingdb/eventsourcingdb \
  --set license.key=${LICENSE_KEY} \
  --set resources.requests.memory=4Gi \
  --set persistence.size=100Gi
```

**Option 2: PostgreSQL Cluster**

```yaml
# PostgreSQL with Patroni for HA
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: myapp-postgres
spec:
  instances: 3
  primaryUpdateStrategy: unsupervised
  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "256MB"
      effective_cache_size: "1GB"
      work_mem: "16MB"
  storage:
    size: 100Gi
    storageClass: fast-ssd
  monitoring:
    enabled: true
  backup:
    retentionPolicy: "30d"
    barmanObjectStore:
      destinationPath: s3://myapp-backups/postgres
      s3Credentials:
        accessKeyId:
          name: aws-credentials
          key: ACCESS_KEY_ID
        secretAccessKey:
          name: aws-credentials
          key: SECRET_ACCESS_KEY
```

### Deployment

**Multi-Region Kubernetes**

```yaml
# Global load balancer
apiVersion: v1
kind: Service
metadata:
  name: myapp-global
  annotations:
    cloud.google.com/load-balancer-type: "External"
spec:
  type: LoadBalancer
  ports:
  - port: 443
    targetPort: 8000
  selector:
    app: myapp

---
# Deployment with autoscaling
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 10
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: myapp:latest
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: myapp-secrets
              key: database-url
        - name: JAEGER_ENDPOINT
          value: "http://jaeger-collector:14268/api/traces"
        - name: OTEL_EXPORTER_OTLP_ENDPOINT
          value: "http://otel-collector:4317"
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 20
          periodSeconds: 5

---
# Horizontal Pod Autoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: myapp-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: myapp
  minReplicas: 10
  maxReplicas: 100
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Observability Stack

**OpenTelemetry Collector**

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024
  
  resource:
    attributes:
    - key: service.name
      value: myapp
      action: upsert

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  
  prometheus:
    endpoint: "0.0.0.0:8889"
  
  logging:
    loglevel: info

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [jaeger]
    
    metrics:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [prometheus]
```

**Prometheus Setup**

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'myapp'
    kubernetes_sd_configs:
    - role: pod
    relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      action: keep
      regex: myapp
    - source_labels: [__meta_kubernetes_pod_ip]
      target_label: __address__
      replacement: '${1}:8000'
    - source_labels: [__meta_kubernetes_pod_name]
      target_label: pod
  
  - job_name: 'otel-collector'
    static_configs:
    - targets: ['otel-collector:8889']
```

**Grafana Dashboards**

```python
# Export metrics for Grafana
from orchestrix.infrastructure import PrometheusMetrics

metrics = PrometheusMetrics(
    namespace="myapp",
    subsystem="orchestrix"
)

# Metrics exposed:
# - myapp_orchestrix_commands_total
# - myapp_orchestrix_events_total
# - myapp_orchestrix_command_duration_seconds
# - myapp_orchestrix_event_handler_duration_seconds
# - myapp_orchestrix_aggregate_load_duration_seconds
# - myapp_orchestrix_event_store_save_duration_seconds
```

### Advanced Features

**Event Replay**

```python
from orchestrix.core import EventReplay

replay = EventReplay(store=store, bus=bus)

# Replay all events for aggregate
await replay.replay_aggregate("ORD-123")

# Replay events in time range
await replay.replay_time_range(
    start=datetime(2024, 1, 1),
    end=datetime(2024, 1, 31)
)

# Replay specific event types
await replay.replay_event_types([OrderCreated, OrderPaid])
```

**Event Encryption**

```python
from orchestrix.core import EncryptedEventStore
from cryptography.fernet import Fernet

# Generate encryption key (store in secrets manager)
key = Fernet.generate_key()

# Wrap store with encryption
encrypted_store = EncryptedEventStore(
    store=store,
    encryption_key=key,
    # Optionally encrypt only sensitive fields
    encrypted_fields=["customer_email", "payment_method"]
)
```

**Multi-Tenancy**

```python
from orchestrix.core import TenantAwareEventStore

# Tenant-isolated event store
tenant_store = TenantAwareEventStore(
    store=store,
    tenant_resolver=lambda: get_current_tenant_id()
)

# Each tenant gets isolated event streams
await tenant_store.save(
    aggregate_id="ORD-123",
    events=[OrderCreated(...)],
    tenant_id="tenant-1"
)
```

**Circuit Breaker**

```python
from orchestrix.core import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,
    recovery_timeout=30
)

# Wrap external service calls
@breaker.protect
async def call_external_service():
    # Call payment gateway, email service, etc.
    pass
```

### Performance Optimization

**Read Model Caching**

```python
from orchestrix.core import CachedProjection
import redis.asyncio as redis

# Redis cache for projections
redis_client = await redis.from_url("redis://localhost:6379")

cached_projection = CachedProjection(
    projection=OrderSummaryProjection(),
    cache=redis_client,
    ttl=300  # 5-minute TTL
)

# Reads hit cache, writes invalidate
summary = await cached_projection.get("ORD-123")
```

**Batch Event Processing**

```python
from orchestrix.core import BatchProcessor

processor = BatchProcessor(
    store=store,
    batch_size=1000,
    max_concurrency=10
)

# Process events in parallel batches
await processor.process(
    projection=OrderAnalyticsProjection(),
    start_position=0
)
```

**Aggregate Caching**

```python
# Cache frequently accessed aggregates
repository = AggregateRepository(
    store=store,
    cache=redis_client,
    cache_ttl=300,
    snapshot_frequency=50
)

# First load: slow (from events)
order = await repository.load("ORD-123", Order)

# Second load: fast (from cache)
order = await repository.load("ORD-123", Order)
```

### Security

**Authentication & Authorization**

```python
from orchestrix.core import SecurityContext

# Attach user context to commands
context = SecurityContext(
    user_id="user-123",
    roles=["admin"],
    permissions=["orders:read", "orders:write"]
)

# Commands include security context
command = CreateOrder(
    order_id="ORD-123",
    customer_name="Alice",
    security_context=context
)

# Verify permissions in handler
class CreateOrderHandler(CommandHandler[CreateOrder]):
    def handle(self, command: CreateOrder) -> None:
        if "orders:write" not in command.security_context.permissions:
            raise PermissionDenied("Insufficient permissions")
        
        # Proceed with command handling
        ...
```

**Event Encryption**

```python
# Encrypt sensitive event data
encrypted_store = EncryptedEventStore(
    store=store,
    encryption_key=get_encryption_key(),
    encrypted_fields=["ssn", "credit_card", "address"]
)
```

**Audit Logging**

```python
from orchestrix.infrastructure import AuditLogger

audit = AuditLogger(
    destination="s3://audit-logs/",
    format="json",
    include_metadata=True
)

bus.add_observability_hook(audit)

# All commands/events logged with:
# - timestamp
# - user_id
# - command/event type
# - aggregate_id
# - full payload
```

### Disaster Recovery

**Backup Strategy**

```bash
# PostgreSQL continuous backup
pg_basebackup -h postgres -U myapp -D /backups/$(date +%Y%m%d)

# EventSourcingDB snapshot
curl -X POST http://eventsourcingdb:2113/admin/backup \
  -H "Authorization: Bearer ${API_KEY}"
```

**Event Store Replication**

```python
# Replicate events to secondary region
from orchestrix.core import EventReplicator

replicator = EventReplicator(
    source_store=primary_store,
    target_store=secondary_store,
    lag_monitoring=True
)

# Continuous replication
await replicator.start()
```

**Point-in-Time Recovery**

```python
# Restore aggregate to specific point in time
from orchestrix.core import PointInTimeRecovery

recovery = PointInTimeRecovery(store=store)

# Restore to January 15th, 2024
order = await recovery.restore(
    aggregate_id="ORD-123",
    timestamp=datetime(2024, 1, 15, 12, 0, 0)
)
```

---

## 🔄 Migration Path

### Small → Medium

**1. Add PostgreSQL**

```bash
# Install PostgreSQL dependency
pip install orchestrix[postgres]
```

```python
# Update infrastructure
from orchestrix.infrastructure import PostgresEventStore, ConnectionPool

pool = ConnectionPool(...)
store = PostgresEventStore(pool)
```

**2. Run Migrations**

```bash
# Create tables
psql -d myapp -f migrations/001_create_events_table.sql
```

**3. Deploy with Database**

```bash
# Update docker-compose.yml to include postgres
docker-compose up -d
```

### Medium → Large

**1. Add Observability**

```bash
pip install orchestrix[observability]
```

```python
# Add tracing and metrics
from orchestrix.infrastructure import OpenTelemetryTracing, PrometheusMetrics

tracing = OpenTelemetryTracing(...)
metrics = PrometheusMetrics(...)

bus.add_observability_hook(tracing)
bus.add_observability_hook(metrics)
```

**2. Deploy Observability Stack**

```bash
# Deploy Jaeger, Prometheus, Grafana
kubectl apply -f k8s/observability/
```

**3. Enable Advanced Features**

```python
# Add dead letter queue
dlq = DeadLetterQueue(...)

# Add circuit breaker
breaker = CircuitBreaker(...)

# Enable caching
repository = AggregateRepository(cache=redis_client, ...)
```

---

## 📝 Configuration Management

### Environment Variables

```bash
# .env.production
DATABASE_URL=postgresql://user:pass@postgres:5432/myapp
REDIS_URL=redis://redis:6379/0
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

# Application settings
SNAPSHOT_FREQUENCY=50
CONNECTION_POOL_MIN=10
CONNECTION_POOL_MAX=50
BATCH_SIZE=1000
CACHE_TTL=300

# Security
ENCRYPTION_KEY=${ENCRYPTION_KEY}
JWT_SECRET=${JWT_SECRET}
```

### Configuration File

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    jaeger_endpoint: str
    
    snapshot_frequency: int = 50
    connection_pool_min: int = 10
    connection_pool_max: int = 50
    batch_size: int = 1000
    cache_ttl: int = 300
    
    encryption_key: str
    jwt_secret: str
    
    class Config:
        env_file = ".env.production"

settings = Settings()
```

---

## 🎯 Best Practices

### Do's ✅

- Start small, scale when needed
- Use PostgreSQL for production (not InMemory)
- Enable observability early (metrics, tracing, logs)
- Implement health checks for Kubernetes
- Use connection pooling
- Enable snapshots for large aggregates
- Test disaster recovery procedures
- Monitor event store performance
- Cache frequently accessed data
- Use circuit breakers for external services

### Don'ts ❌

- Don't use InMemoryEventStore in production
- Don't deploy without health checks
- Don't skip database migrations
- Don't ignore backup strategy
- Don't hardcode secrets in code
- Don't deploy without monitoring
- Don't skip load testing
- Don't ignore security (encryption, audit logs)
- Don't over-optimize prematurely
- Don't deploy without rollback plan

---

## 🔗 See Also

- [Production Readiness Guide](production-ready.md) - Complete production checklist
- [Best Practices](best-practices.md) - Domain modeling and error handling
- [Tracing Examples](../examples/tracing.md) - Observability examples
- [Metrics Examples](../examples/metrics.md) - Prometheus metrics setup

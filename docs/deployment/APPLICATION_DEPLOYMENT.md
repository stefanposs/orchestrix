# Application Deployment Guide (Production)

This guide covers deploying Orchestrix applications in production environments, including containerization, orchestration, monitoring, security, and performance optimization.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment](#docker-deployment)
3. [Kubernetes Deployment](#kubernetes-deployment)
4. [Event Store Selection](#event-store-selection)
5. [Monitoring & Observability](#monitoring--observability)
6. [Security Considerations](#security-considerations)
7. [Performance Tuning](#performance-tuning)
8. [High Availability](#high-availability)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### Production Checklist

- [ ] Python 3.12+ installed
- [ ] All tests passing (`pytest tests/`)
- [ ] Code quality checks passing (`ruff check`)
- [ ] Production event store selected (PostgreSQL or EventSourcingDB)
- [ ] Monitoring/logging infrastructure ready
- [ ] Security review completed
- [ ] Load testing performed
- [ ] Backup strategy defined
- [ ] Incident response plan documented

### Recommended Infrastructure

**Minimum Production Setup:**
- 2 CPU cores per service
- 4 GB RAM per service
- Persistent storage for event store
- Load balancer (for multi-instance deployments)
- Monitoring system (Prometheus/Grafana or cloud-native)

## Docker Deployment

### Basic Dockerfile

Create a production-optimized Dockerfile:

```dockerfile
# Use official Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN useradd -m -u 1000 orchestrix && \
    chown -R orchestrix:orchestrix /app
USER orchestrix

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import orchestrix; print('OK')" || exit 1

# Run application
CMD ["python", "-m", "your_app.main"]
```

### Multi-stage Build (Optimized)

For smaller image sizes:

```dockerfile
# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir build && \
    python -m build

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy built wheel from builder
COPY --from=builder /app/dist/*.whl .
RUN pip install --no-cache-dir *.whl && rm *.whl

# Create non-root user
RUN useradd -m -u 1000 orchestrix
USER orchestrix

CMD ["python", "-m", "your_app.main"]
```

### Docker Compose

For local testing with PostgreSQL:

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://orchestrix:secret@postgres:5432/orchestrix
      - LOG_LEVEL=INFO
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=orchestrix
      - POSTGRES_PASSWORD=secret
      - POSTGRES_DB=orchestrix
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U orchestrix"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  postgres_data:
```

### EventSourcingDB Deployment

With EventSourcingDB:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - EVENTSOURCINGDB_URL=http://eventsourcingdb:3000
      - EVENTSOURCINGDB_TOKEN=${EVENTSOURCINGDB_TOKEN}
      - LOG_LEVEL=INFO
    depends_on:
      eventsourcingdb:
        condition: service_healthy
    restart: unless-stopped

  eventsourcingdb:
    image: thenativeweb/eventsourcingdb:latest
    ports:
      - "3000:3000"
    environment:
      - API_TOKEN=${EVENTSOURCINGDB_TOKEN}
    volumes:
      - eventsourcingdb_data:/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:3000/api/v1/ping || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

volumes:
  eventsourcingdb_data:
```

## Kubernetes Deployment

### Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: orchestrix-prod
  labels:
    name: orchestrix-prod
```

### ConfigMap

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: orchestrix-config
  namespace: orchestrix-prod
data:
  LOG_LEVEL: "INFO"
  WORKERS: "4"
  MAX_RETRIES: "3"
```

### Secret

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: orchestrix-secrets
  namespace: orchestrix-prod
type: Opaque
data:
  # Base64 encoded values
  database-url: <base64-encoded-connection-string>
  eventsourcingdb-token: <base64-encoded-token>
```

Create secrets:
```bash
kubectl create secret generic orchestrix-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=eventsourcingdb-token="your-token" \
  -n orchestrix-prod
```

### Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: orchestrix-app
  namespace: orchestrix-prod
  labels:
    app: orchestrix
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: orchestrix
  template:
    metadata:
      labels:
        app: orchestrix
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: orchestrix
        image: your-registry/orchestrix:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: orchestrix-secrets
              key: database-url
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: orchestrix-config
              key: LOG_LEVEL
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
        securityContext:
          runAsNonRoot: true
          runAsUser: 1000
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - orchestrix
              topologyKey: kubernetes.io/hostname
```

### Service

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: orchestrix-service
  namespace: orchestrix-prod
  labels:
    app: orchestrix
spec:
  type: ClusterIP
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: orchestrix
```

### Ingress

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: orchestrix-ingress
  namespace: orchestrix-prod
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - orchestrix.yourdomain.com
    secretName: orchestrix-tls
  rules:
  - host: orchestrix.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: orchestrix-service
            port:
              number: 80
```

### HorizontalPodAutoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orchestrix-hpa
  namespace: orchestrix-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: orchestrix-app
  minReplicas: 3
  maxReplicas: 10
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

### Deploy to Kubernetes

```bash
# Apply all configurations
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f hpa.yaml

# Verify deployment
kubectl get pods -n orchestrix-prod
kubectl logs -f deployment/orchestrix-app -n orchestrix-prod

# Check rollout status
kubectl rollout status deployment/orchestrix-app -n orchestrix-prod
```

## Event Store Selection

### InMemory (Development Only)

**Use Case:** Local development, unit tests

```python
from orchestrix.infrastructure import InMemoryEventStore

store = InMemoryEventStore()
```

**Limitations:**
- ❌ Data lost on restart
- ❌ No persistence
- ❌ Not production-ready

### PostgreSQL (Production)

**Use Case:** Production deployments, transaction support, SQL queries

```python
from orchestrix.infrastructure import PostgreSQLEventStore

store = PostgreSQLEventStore(
    connection_string="postgresql://user:pass@host:5432/db"
)
await store.initialize()
```

**Advantages:**
- ✅ Mature, battle-tested
- ✅ ACID transactions
- ✅ Strong consistency
- ✅ Rich query capabilities (SQL)
- ✅ Excellent tooling

**Configuration:**
- Connection pooling (min: 10, max: 50)
- Statement timeout: 30s
- Lock timeout: 10s
- Work memory: 256MB

### EventSourcingDB (Production)

**Use Case:** CloudEvents-native, event sourcing optimized

```python
from orchestrix.infrastructure import EventSourcingDBStore

store = EventSourcingDBStore(
    base_url="http://eventsourcingdb:3000",
    api_token="your-secret-token"
)
```

**Advantages:**
- ✅ CloudEvents native (perfect fit)
- ✅ Purpose-built for event sourcing
- ✅ Built-in snapshots
- ✅ Preconditions (optimistic concurrency)
- ✅ EventQL query language
- ✅ Minimal ops overhead

**Licensing:**
- Free tier: ≤25,000 events
- Commercial: >25,000 events (per instance/year)

### Comparison Matrix

| Feature | InMemory | PostgreSQL | EventSourcingDB |
|---------|----------|------------|-----------------|
| Production Ready | ❌ | ✅ | ✅ |
| CloudEvents Native | ✅ | ⚠️ (JSONB) | ✅ |
| Persistence | ❌ | ✅ | ✅ |
| Transactions | ❌ | ✅ | ✅ |
| Query Language | Python | SQL | EventQL |
| Snapshots | ✅ | Custom | ✅ |
| Optimistic Locking | ❌ | ✅ | ✅ |
| Setup Complexity | None | Medium | Low |
| Ops Overhead | None | Medium | Low |
| Cost | Free | Infrastructure | Free <25k, license >25k |

## Monitoring & Observability

### Structured Logging

Orchestrix uses structured logging by default:

```python
from orchestrix.logging import get_logger

logger = get_logger(__name__)

logger.info(
    "Order created",
    order_id="ORD-001",
    customer_name="Alice",
    total_amount=149.99
)
```

**Log Levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational events
- `WARNING`: Warning messages (degraded but working)
- `ERROR`: Error events (operation failed)

### Prometheus Metrics (Future)

When available via `pip install orchestrix[metrics]`:

```python
from orchestrix.metrics import MetricsCollector

metrics = MetricsCollector(port=9090)
metrics.register(bus)
```

**Key Metrics:**
- `orchestrix_messages_published_total` - Total messages published
- `orchestrix_messages_processed_total` - Total messages processed
- `orchestrix_handler_duration_seconds` - Handler execution time
- `orchestrix_handler_errors_total` - Handler errors
- `orchestrix_eventstore_read_duration_seconds` - Event store read latency
- `orchestrix_eventstore_write_duration_seconds` - Event store write latency

### OpenTelemetry Tracing (Future)

When available via `pip install orchestrix[tracing]`:

```python
from orchestrix.tracing import TracingMiddleware

tracing = TracingMiddleware(
    service_name="orchestrix-app",
    endpoint="http://jaeger:4318"
)
tracing.register(bus)
```

**Trace Attributes:**
- `message.id` - CloudEvents message ID
- `message.type` - Message type
- `message.source` - Message source
- `aggregate.id` - Aggregate identifier
- `handler.name` - Handler function name

### Health Checks

Implement health endpoints:

```python
from orchestrix.infrastructure import InMemoryMessageBus, PostgreSQLEventStore
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    """Liveness probe - process is alive"""
    return {"status": "healthy"}

@app.get("/ready")
async def readiness_check(store: PostgreSQLEventStore):
    """Readiness probe - ready to serve traffic"""
    try:
        # Check event store connectivity
        await store.ping()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503
```

### Log Aggregation

**Recommended Stack:**

1. **ELK Stack** (Elasticsearch, Logstash, Kibana)
2. **Loki** (Grafana Loki) - Lightweight alternative
3. **CloudWatch** / **Stackdriver** - Cloud-native

**Log Format:**
```json
{
  "timestamp": "2026-01-03T18:30:00Z",
  "level": "INFO",
  "logger": "orchestrix.infrastructure.inmemory_bus",
  "message": "Publishing message",
  "message_type": "CreateOrder",
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "handler_count": 2
}
```

## Security Considerations

### Authentication & Authorization

**API Token Management:**

```python
import os
from orchestrix.infrastructure import EventSourcingDBStore

# Use environment variables
token = os.getenv("EVENTSOURCINGDB_TOKEN")
if not token:
    raise ValueError("EVENTSOURCINGDB_TOKEN not set")

store = EventSourcingDBStore(
    base_url=os.getenv("EVENTSOURCINGDB_URL"),
    api_token=token
)
```

### Secrets Management

**Kubernetes Secrets:**
```bash
# Create from file
kubectl create secret generic orchestrix-secrets \
  --from-file=api-token=./token.txt \
  -n orchestrix-prod

# Create from literal
kubectl create secret generic orchestrix-secrets \
  --from-literal=api-token="your-secret-token" \
  -n orchestrix-prod
```

**External Secrets Operator:**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: orchestrix-secrets
spec:
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: orchestrix-secrets
  data:
  - secretKey: api-token
    remoteRef:
      key: orchestrix/api-token
```

### Network Security

**Network Policies:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: orchestrix-network-policy
  namespace: orchestrix-prod
spec:
  podSelector:
    matchLabels:
      app: orchestrix
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - namespaceSelector: {}
      podSelector:
        matchLabels:
          app: eventsourcingdb
    ports:
    - protocol: TCP
      port: 3000
```

### Data Encryption

**At Rest:**
- PostgreSQL: Enable TLS for connections
- EventSourcingDB: Use encrypted volumes
- Kubernetes: Enable encryption at rest for secrets

**In Transit:**
```python
# PostgreSQL with SSL
connection_string = "postgresql://user:pass@host:5432/db?sslmode=require"

# EventSourcingDB with HTTPS
store = EventSourcingDBStore(
    base_url="https://eventsourcingdb.internal",
    api_token=token
)
```

### Security Checklist

- [ ] All secrets in secure stores (not hardcoded)
- [ ] TLS/SSL enabled for all connections
- [ ] Network policies configured
- [ ] Non-root containers
- [ ] Read-only root filesystem where possible
- [ ] Security scanning in CI/CD
- [ ] Dependency vulnerability scanning
- [ ] Regular security updates
- [ ] Audit logging enabled
- [ ] Rate limiting configured

## Performance Tuning

### Message Bus Optimization

**Batch Publishing:**

```python
# ❌ Inefficient - multiple publishes
for event in events:
    await bus.publish(event)

# ✅ Efficient - batch publish
await bus.publish_batch(events)
```

**Handler Parallelization:**

Use `InMemoryAsyncMessageBus` for concurrent execution:

```python
from orchestrix.infrastructure import InMemoryAsyncMessageBus

bus = InMemoryAsyncMessageBus()

# Handlers execute concurrently
bus.subscribe(OrderCreated, update_inventory_handler)
bus.subscribe(OrderCreated, send_email_handler)
bus.subscribe(OrderCreated, update_analytics_handler)

await bus.publish(event)  # All 3 handlers run in parallel
```

### Event Store Optimization

**PostgreSQL Tuning:**

```sql
-- Indexes for fast queries
CREATE INDEX idx_events_aggregate_id ON events(aggregate_id);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_timestamp ON events(timestamp);

-- Partitioning by date
CREATE TABLE events_2026_01 PARTITION OF events
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
```

**Connection Pooling:**

```python
from orchestrix.infrastructure import PostgreSQLEventStore

store = PostgreSQLEventStore(
    connection_string="postgresql://...",
    pool_min_size=10,
    pool_max_size=50,
    pool_timeout=30.0
)
```

**Snapshot Strategy:**

```python
from orchestrix.snapshot import Snapshot

# Take snapshots every 100 events
if len(events) % 100 == 0:
    snapshot = Snapshot(
        aggregate_id=aggregate.id,
        aggregate_type="Order",
        version=len(events),
        state=aggregate.to_dict()
    )
    await store.save_snapshot(snapshot)
```

### Resource Limits

**Kubernetes Resources:**

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

**Python Process Tuning:**

```bash
# Set worker processes
export WORKERS=4

# Limit memory per worker
export MEMORY_LIMIT_MB=1024

# Asyncio event loop tuning
export PYTHONUNBUFFERED=1
```

### Benchmarking

Run benchmarks to establish baselines:

```bash
# Install benchmark dependencies
pip install orchestrix[benchmark]

# Run benchmarks
pytest tests/benchmarks/ --benchmark-only

# Generate report
pytest tests/benchmarks/ --benchmark-autosave --benchmark-histogram
```

## High Availability

### Multi-Region Deployment

**Active-Passive:**

```
Region 1 (Active)     Region 2 (Passive)
     ├── App             ├── App (standby)
     ├── PostgreSQL      └── PostgreSQL (replica)
     └── Load Balancer
```

**Active-Active:**

```
Region 1              Region 2
     ├── App               ├── App
     ├── PostgreSQL        ├── PostgreSQL
     └── Load Balancer     └── Load Balancer
              ↓                    ↓
           Global Load Balancer
```

### Database Replication

**PostgreSQL Streaming Replication:**

```bash
# Primary
wal_level = replica
max_wal_senders = 10
max_replication_slots = 10
synchronous_commit = on

# Replica
hot_standby = on
```

**EventSourcingDB:**

Refer to EventSourcingDB documentation for clustering and replication strategies.

### Backup Strategy

**PostgreSQL Backups:**

```bash
# Full backup
pg_dump orchestrix > backup_$(date +%Y%m%d).sql

# Continuous archiving
archive_mode = on
archive_command = 'cp %p /backup/archive/%f'

# Point-in-time recovery
pg_basebackup -D /backup/base
```

**EventSourcingDB Backups:**

```bash
# Data directory backup
docker exec eventsourcingdb tar czf - /data > backup.tar.gz

# Restore
docker exec -i eventsourcingdb tar xzf - -C / < backup.tar.gz
```

**Backup Schedule:**
- Full backups: Daily at 2 AM
- Incremental: Every 4 hours
- Retention: 30 days
- Test restores: Weekly

## Troubleshooting

### Common Issues

#### 1. High Memory Usage

**Symptoms:**
- OOMKilled pods
- Slow response times
- Memory warnings in logs

**Solutions:**
- Increase memory limits
- Implement event stream pagination
- Use snapshots to reduce event replay size
- Profile memory usage: `memory_profiler`

#### 2. Handler Timeouts

**Symptoms:**
- HandlerError exceptions
- Incomplete event processing

**Solutions:**
- Increase handler timeout
- Optimize handler logic
- Use retry policies
- Move to async handlers

#### 3. Event Store Connection Failures

**Symptoms:**
- Connection refused errors
- Timeout errors

**Solutions:**
- Check network connectivity
- Verify credentials
- Increase connection pool size
- Enable connection retry logic

#### 4. Message Processing Delays

**Symptoms:**
- Events not processed
- Long delays between publish and handling

**Solutions:**
- Switch to `InMemoryAsyncMessageBus`
- Increase worker processes
- Profile handler execution time
- Check for blocking I/O in handlers

### Debug Mode

Enable debug logging:

```python
import logging
from orchestrix.logging import get_logger

# Set to DEBUG level
logging.basicConfig(level=logging.DEBUG)

logger = get_logger(__name__)
```

### Monitoring Commands

```bash
# Kubernetes
kubectl top pods -n orchestrix-prod
kubectl logs -f deployment/orchestrix-app -n orchestrix-prod
kubectl describe pod <pod-name> -n orchestrix-prod

# Docker
docker stats
docker logs -f orchestrix-app
docker inspect orchestrix-app

# PostgreSQL
psql -c "SELECT * FROM pg_stat_activity;"
psql -c "SELECT pg_size_pretty(pg_database_size('orchestrix'));"

# EventSourcingDB
curl http://localhost:3000/api/v1/ping
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:3000/api/v1/read-subjects -d '{"baseSubject":"/"}'
```

## Production Checklist

### Pre-Deployment

- [ ] All tests passing (unit, integration, e2e)
- [ ] Load testing completed
- [ ] Security scan passed
- [ ] Documentation updated
- [ ] Secrets configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Rollback plan documented

### During Deployment

- [ ] Blue-green or canary deployment
- [ ] Health checks passing
- [ ] Metrics being collected
- [ ] Logs being aggregated
- [ ] No error spikes
- [ ] Performance within baseline

### Post-Deployment

- [ ] Smoke tests passed
- [ ] Monitor for 1 hour
- [ ] Check error rates
- [ ] Verify event processing
- [ ] Customer-facing features working
- [ ] Document any issues
- [ ] Update runbook

## Support & Resources

- [Orchestrix Documentation](https://github.com/stefanposs/orchestrix)
- [Issue Tracker](https://github.com/stefanposs/orchestrix/issues)
- [Security Policy](.github/SECURITY.md)
- [Contributing Guide](.github/CONTRIBUTING.md)

For production support inquiries, contact: stefan@example.com

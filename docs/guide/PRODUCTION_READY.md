# Production Readiness Guide

## Overview

This guide provides comprehensive guidance for deploying and operating Orchestrix in production environments. Orchestrix is a protocol-based event sourcing and CQRS platform designed for building scalable, maintainable domain-driven systems.

## Architecture & Design

### Core Principles

- **Event Sourcing**: All state changes are captured as immutable events
- **CQRS**: Commands modify state, queries read snapshots/views
- **Protocol-Based Design**: Leverages Python Protocols for loose coupling
- **CloudEvents Compatible**: Events use CloudEvents specification for interoperability
- **Async-First**: Full support for async/await throughout the stack

### Key Components

1. **AggregateRoot**: Domain model with event handlers
2. **AggregateRepository**: Persistence layer with automatic event replay
3. **MessageBus**: Publish/subscribe for domain and integration events
4. **EventStore**: Pluggable persistence (InMemory, PostgreSQL, EventSourcingDB)
5. **Snapshot**: Performance optimization for large event streams
6. **Observability Hooks**: Metrics, tracing, and error tracking

## Deployment

### System Requirements

- **Python**: 3.12+ (3.13 recommended)
- **Database**: PostgreSQL 14+ (for production event store)
- **Memory**: 512MB minimum, 2GB+ recommended
- **CPU**: Single core minimum, multi-core recommended for async workloads

### Environment Setup

```bash
# 1. Clone repository
git clone <repo-url>
cd orchestrix

# 2. Create virtual environment
python3.13 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
uv pip install -e ".[postgres]"  # with PostgreSQL support
# or
uv pip install -e .  # minimal

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your settings
```

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/orchestrix
DATABASE_POOL_SIZE=20
DATABASE_TIMEOUT=30

# Event Store Configuration
EVENT_STORE_TYPE=postgres  # inmemory, postgres, eventsourcingdb
SNAPSHOT_INTERVAL=100  # Save snapshot every N events

# Observability
LOG_LEVEL=INFO
METRICS_ENABLED=true
TRACING_ENABLED=false
JAEGER_ENDPOINT=http://localhost:6831

# Application
DEBUG=false
ENVIRONMENT=production
```

### Docker Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY . .
RUN pip install -e ".[postgres]"

# Run application
CMD ["python", "-m", "orchestrix.main"]
```

**Docker Compose Example**:

```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      DATABASE_URL: postgresql://user:password@postgres:5432/orchestrix
    depends_on:
      - postgres
    ports:
      - "8000:8000"

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: orchestrix
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Configuration

### Event Store Selection

#### InMemory (Development/Testing)
```python
from orchestrix.infrastructure import InMemoryEventStore

store = InMemoryEventStore()  # All events in RAM
```

**Pros**: Fast, no external dependencies
**Cons**: No persistence, data lost on restart, not thread-safe

#### PostgreSQL (Production)
```python
from orchestrix.infrastructure import PostgresEventStore

store = PostgresEventStore(
    connection_string="postgresql://localhost/orchestrix",
    pool_size=20
)
```

**Pros**: ACID compliance, scalable, production-ready
**Cons**: Network latency, requires external database

**Setup**:
```sql
-- Create database
CREATE DATABASE orchestrix;

-- Create events table (auto-migrated by Orchestrix)
-- Run: orchestrix migrate
```

#### EventSourcingDB (Event Store Database)
```python
from orchestrix.infrastructure import EventSourcingDBStore

store = EventSourcingDBStore(
    url="http://localhost:2113",
    stream_name="orchestrix"
)
```

**Pros**: Purpose-built for event sourcing, excellent tooling
**Cons**: Requires separate service, more complex operations

### Snapshot Configuration

Enable snapshots to improve load performance:

```python
from orchestrix.core import AggregateRepository
from orchestrix.infrastructure import InMemoryEventStore, InMemorySnapshotStore

repository = AggregateRepository(
    event_store=InMemoryEventStore(),
    snapshot_store=InMemorySnapshotStore(),
    snapshot_interval=100  # Save snapshot every 100 events
)
```

**Guidelines**:
- Use snapshots for aggregates with >50 events in typical load
- Set interval based on event size and replay performance
- Monitor event load times to tune interval

## Observability

### Logging

Orchestrix uses Python's standard logging with structured context:

```python
from orchestrix.core.logging import get_logger

logger = get_logger(__name__)

# Structured logging with context
logger.info(
    "Aggregate loaded",
    extra={
        "aggregate_id": "user-123",
        "version": 42,
        "event_count": 15
    }
)
```

**Configuration**:
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Metrics & Tracing

Orchestrix provides extensible observability hooks:

```python
from orchestrix.core.observability import init_observability

# Initialize with custom providers (e.g., Prometheus, Jaeger)
observability = init_observability(
    metrics_provider=MyPrometheusProvider(),
    tracing_provider=MyJaegerProvider()
)

# Hooks automatically called during operations
# - record_event_stored()
# - record_event_loaded()
# - record_event_replayed()
# - record_snapshot_saved/loaded()
# - record_aggregate_error()
```

**Example: Prometheus Integration**:

```python
from prometheus_client import Counter, Histogram
from orchestrix.core.observability import MetricsProvider

class PrometheusMetrics(MetricsProvider):
    def __init__(self):
        self.events_stored = Counter(
            'orchestrix_events_stored_total',
            'Events stored',
            ['aggregate_id']
        )
        self.event_load_time = Histogram(
            'orchestrix_event_load_time_seconds',
            'Time to load events'
        )
    
    def counter(self, name, value=1.0, labels=None):
        if 'events_stored' in name:
            self.events_stored.labels(**labels).inc(value)
    
    # ... implement other methods
```

### Health Checks

```python
async def health_check(repository: AggregateRepository) -> dict:
    """Check system health."""
    try:
        # Verify event store connectivity
        test_id = "health-check"
        
        # Try loading (may not exist)
        try:
            await repository.load_async(MyAggregate, test_id)
        except:
            pass  # Expected if test aggregate doesn't exist
        
        return {
            "status": "healthy",
            "event_store": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
```

## Error Handling

### Common Issues & Solutions

#### 1. Event Store Connection Failed
```
Error: Unable to connect to PostgreSQL
Solution:
1. Verify DATABASE_URL is correct
2. Check PostgreSQL is running: psql -U user -d orchestrix
3. Verify credentials and firewall rules
4. Check connection pool limits
```

#### 2. Snapshot Inconsistency
```
Error: Snapshot version mismatch
Solution:
1. Clear snapshots: TRUNCATE snapshots;
2. Rebuild from events: orchestrix rebuild-snapshots
3. Verify event ordering in database
```

#### 3. Memory Growth in Event Store
```
Issue: InMemory store consuming too much memory
Solution:
1. Switch to PostgreSQL for production
2. Implement snapshots to reduce event streams
3. Archive old events periodically
```

#### 4. Slow Event Replay
```
Symptoms: Slow aggregate loading, high CPU
Solutions:
1. Enable/optimize snapshots (reduce replay chain)
2. Check database indexing on event_id, aggregate_id
3. Monitor event size - large payloads slow replay
4. Use read replicas for high-traffic services
```

### Error Tracking

Use the observability hooks to track errors:

```python
from orchestrix.core.observability import get_observability

observability = get_observability()

# Register error callback
def on_error(aggregate_id: str, error: str):
    sentry.capture_exception(error)
    alert.notify(f"Error processing {aggregate_id}: {error}")

observability.on_aggregate_error(on_error)
```

## Database Maintenance

### PostgreSQL

```sql
-- Create indexes for performance
CREATE INDEX idx_events_aggregate_id ON events(aggregate_id);
CREATE INDEX idx_events_timestamp ON events(timestamp);
CREATE INDEX idx_snapshots_aggregate_id ON snapshots(aggregate_id);

-- Monitor event growth
SELECT COUNT(*) as total_events,
       COUNT(DISTINCT aggregate_id) as aggregates
FROM events;

-- Archive old events (optional)
-- Keep recent events hot, archive older ones
CREATE TABLE events_archive AS 
SELECT * FROM events 
WHERE timestamp < NOW() - INTERVAL '1 year';

DELETE FROM events 
WHERE timestamp < NOW() - INTERVAL '1 year';

-- Vacuum to reclaim space
VACUUM ANALYZE;
```

### Backup & Recovery

```bash
# Backup PostgreSQL
pg_dump -U user orchestrix > orchestrix_backup.sql

# Restore from backup
psql -U user orchestrix < orchestrix_backup.sql

# Backup snapshot tables
pg_dump -U user orchestrix -t snapshots > snapshots_backup.sql

# Point-in-time recovery
pg_restore --recovery-target-time='2024-01-03 15:30:00' ...
```

## Performance Tuning

### Connection Pooling

```python
from orchestrix.infrastructure import PostgresEventStore

store = PostgresEventStore(
    connection_string="postgresql://localhost/orchestrix",
    pool_size=20,  # Connections in pool
    pool_recycle=3600,  # Recycle after 1 hour
    pool_timeout=30,  # Wait 30s for available connection
    max_overflow=10  # Allow temporary overflow
)
```

**Guidelines**:
- pool_size = (CPU cores × 2) + 1
- Increase for high concurrency, decrease for limited connections
- Monitor connection usage: `SELECT count(*) FROM pg_stat_activity;`

### Event Batch Processing

```python
async def process_events_batch(
    repository: AggregateRepository,
    aggregate_ids: list[str],
    batch_size: int = 100
):
    """Process multiple aggregates efficiently."""
    for i in range(0, len(aggregate_ids), batch_size):
        batch = aggregate_ids[i:i + batch_size]
        
        # Process in parallel
        tasks = [
            repository.load_async(MyAggregate, agg_id)
            for agg_id in batch
        ]
        
        aggregates = await asyncio.gather(*tasks)
        
        # Process results
        for aggregate in aggregates:
            await handle_aggregate(aggregate)
```

### Caching Strategy

```python
from functools import lru_cache

class CachedRepository:
    def __init__(self, repository: AggregateRepository):
        self.repository = repository
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def load_with_cache(self, agg_type, agg_id):
        """Load with caching."""
        cache_key = f"{agg_type.__name__}:{agg_id}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        aggregate = await self.repository.load_async(agg_type, agg_id)
        self._cache[cache_key] = aggregate
        
        return aggregate
```

## Security

### Input Validation

All command inputs should be validated:

```python
from orchestrix.core import AggregateRoot
from pydantic import BaseModel, validator

class CreateUserCommand(BaseModel):
    email: str
    name: str
    
    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v

class UserAggregate(AggregateRoot):
    def create_user(self, cmd: CreateUserCommand):
        # Command already validated by Pydantic
        self.emit("UserCreated", email=cmd.email, name=cmd.name)
```

### Database Security

```python
# Use parameterized queries (automatic with ORM)
# Never concatenate user input into SQL

# Example: WRONG ❌
# query = f"SELECT * FROM events WHERE id = {user_input}"

# Example: RIGHT ✅
# query = "SELECT * FROM events WHERE id = %s"
# execute(query, (user_input,))

# PostgreSQL-specific
- Use different roles for read/write
- Restrict snapshot storage to read-only replicas
- Enable SSL/TLS for connections
- Use secrets management (Vault, AWS Secrets Manager)
```

### Event Content

```python
# Sensitive data in events
# - Store only what's necessary
# - Use references instead of full data
# - Implement event encryption for sensitive domains

class BankTransferAggregate(AggregateRoot):
    def transfer(self, amount: float, from_account: str, to_account: str):
        # ✅ GOOD: Hash account numbers
        self.emit("MoneyTransferred", 
                 amount=amount,
                 from_hash=hash(from_account),
                 to_hash=hash(to_account))
        
        # ❌ BAD: Store full account details
        # self.emit("MoneyTransferred",
        #          amount=amount,
        #          from_account=from_account,
        #          to_account=to_account)
```

## Scaling

### Horizontal Scaling

```python
# Application instances behind load balancer
# - All read from shared PostgreSQL event store
# - Snapshots ensure fast loading regardless of instance
# - Message bus handles distributed events

# Load balancer config (nginx example):
upstream orchestrix {
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://orchestrix;
    }
}
```

### Event Store Scaling

```
PostgreSQL Scaling Options:
1. Vertical: More CPU, memory, storage (simple, limited)
2. Read replicas: Secondary servers for reads
3. Sharding: Split events by aggregate_id range
4. EventSourcingDB: Purpose-built for event sourcing
```

### Async Processing

```python
# Offload long-running operations
async def submit_payment(aggregate: BankTransferAggregate):
    # Emit event
    aggregate.process_payment()
    
    # Save
    await repository.save_async(aggregate)
    
    # Async notification (don't wait)
    asyncio.create_task(notify_user(aggregate.id))
```

## Monitoring Checklist

- [ ] Event store connectivity (health checks)
- [ ] Event processing latency (P50, P95, P99)
- [ ] Snapshot hit rate (should be >80% with proper tuning)
- [ ] Database connection pool utilization
- [ ] Error rates and error types
- [ ] Memory usage (watch for event accumulation)
- [ ] Query performance (slow queries log)
- [ ] Backup completion and restoration tests

## Recovery Procedures

### Disaster Recovery

```bash
# 1. Stop application
docker-compose down

# 2. Restore database from backup
psql orchestrix < backup.sql

# 3. Verify data integrity
SELECT COUNT(*) FROM events;

# 4. Restart application
docker-compose up -d

# 5. Verify operation
curl http://localhost:8000/health
```

### Rollback Strategy

Event sourcing provides built-in versioning:

```python
# Load specific event version
events = await store.load("aggregate-id")
# Filter: events up to specific timestamp or version

# Rebuild aggregate at point in time
aggregate = await repository.load_at_version(
    AggregateType, 
    "aggregate-id",
    version=42
)
```

## Production Deployment Checklist

- [ ] PostgreSQL database configured with backups
- [ ] Connection pooling configured appropriately
- [ ] Observability hooks wired to monitoring system
- [ ] Health checks implemented and monitored
- [ ] Error tracking (Sentry, DataDog, etc) configured
- [ ] Logging configured with centralized collection (ELK, Splunk)
- [ ] Database indexing applied
- [ ] Snapshot intervals tuned for workload
- [ ] Load testing completed (expected throughput verified)
- [ ] Disaster recovery plan documented and tested
- [ ] Security review completed (input validation, secrets)
- [ ] Runbook created for common issues
- [ ] Team trained on operation and troubleshooting

## Support & Resources

- **Documentation**: See docs/ folder for API and architecture details
- **Examples**: See examples/ for complete working applications
- **Issues**: Report bugs and feature requests on GitHub
- **Community**: Discussions and best practices

---

**Last Updated**: January 2025
**Version**: 1.0

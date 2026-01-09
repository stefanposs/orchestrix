# Orchestrix TODO & Roadmap

## Decision Required: Cloud & Integration Services

Should Orchestrix provide technical implementations for the following services?

### Monitoring & Error Tracking
- [ ] **Sentry Integration** - Error tracking and performance monitoring
  - Event/command error capture
  - Saga failure tracking
  - Performance transaction tracing
  - Breadcrumbs for event flow

### Data & Storage Services
- [X] **Google BigQuery** - Event store backend for analytics
  - Stream events to BigQuery tables
  - Time-series event analysis
  - SQL-based projections
  - Data warehouse integration

- [ ] **Google Cloud Storage** - Snapshot storage backend
  - Store large snapshots in GCS buckets
  - Versioned snapshot archives
  - Cost-effective long-term storage
  - Integration with lifecycle policies

- [ ] **Google Cloud SQL** - Managed PostgreSQL backend
  - Ready-to-use Cloud SQL configuration
  - Automated backups integration
  - High availability setup
  - Connection pooling optimization

### Messaging & Communication
- [X] **Google Pub/Sub** - Message bus integration
  - Publish events to Pub/Sub topics
  - Subscribe to external event streams
  - Dead letter topic configuration
  - Exactly-once delivery guarantees

- [ ] **SendGrid** - Email notification handler
  - Email-based event notifications
  - Transactional email saga steps
  - Template-based messaging
  - Delivery tracking and webhooks

**Decision Criteria:**
- Should we be opinionated with batteries-included integrations?
- Or stay lightweight and let users implement their own adapters?
- Trade-off: Convenience vs. Maintenance burden vs. Dependency bloat

---

## DevOps & Automation

### GitHub Actions Workflows
- [X] **Dependabot Configuration**
  - Automated dependency updates
  - Security vulnerability scanning
  - Python package updates
  - GitHub Actions version updates

- [X] **Enhanced QA Pipeline**
  - Matrix testing (Python 3.11, 3.12, 3.13)
  - OS matrix (Ubuntu, macOS, Windows)
  - Coverage reporting to Codecov
  - Performance regression detection

- [X] **PyPI Publishing Automation**
  - Automated releases on git tags
  - Version bump automation
  - Changelog generation
  - Test PyPI deployment
  - Signed releases with Sigstore

- [X] **Documentation Deployment**
  - Auto-deploy docs on main branch
  - Preview docs for PRs
  - Version-specific documentation

---

## Feature Ideas & Enhancements

### Core Framework
- [ ] **Event Replay System**
  - Replay events for debugging
  - Time-travel debugging
  - Event filtering and transformation
  - Replay to specific timestamp

- [ ] **Multi-Tenant Support**
  - Tenant-aware event stores
  - Isolated event streams per tenant
  - Tenant-specific projections
  - Cross-tenant saga coordination

- [ ] **Event Encryption**
  - At-rest encryption for sensitive events
  - Field-level encryption
  - Key rotation support
  - Integration with KMS (AWS, GCP, Azure)

- [ ] **Schema Registry Integration**
  - Confluent Schema Registry support
  - Avro/Protobuf event serialization
  - Schema evolution validation
  - Version compatibility checks

### Event Store Backends
- [ ] **MongoDB Backend**
  - Document-based event storage
  - Change streams for projections
  - Sharding support

- [ ] **DynamoDB Backend** (AWS)
  - Serverless event store
  - Pay-per-request pricing
  - Global tables for multi-region

- [ ] **Cosmos DB Backend** (Azure)
  - Multi-model database support
  - Change feed integration
  - Global distribution

- [ ] **Apache Kafka Backend**
  - Event log as event store
  - Compaction for snapshots
  - Consumer groups for projections

### Projection Backends
- [ ] **Redis Projections**
  - Fast in-memory read models
  - Pub/Sub for real-time updates
  - Redis Streams integration

- [ ] **Elasticsearch Projections**
  - Full-text search on events
  - Complex aggregations
  - Kibana dashboard integration

- [ ] **Apache Cassandra**
  - Time-series event queries
  - Wide-column projections
  - Linear scalability

### Saga Enhancements
- [ ] **Parallel Saga Steps**
  - Execute independent steps concurrently
  - Wait for all completion
  - Partial compensation on failure

- [ ] **Saga Timeouts**
  - Step-level timeout configuration
  - Automatic compensation on timeout
  - Configurable retry with backoff

- [ ] **Saga Orchestration UI**
  - Visual saga designer
  - Real-time saga execution tracking
  - Failed saga retry interface

### Developer Experience
- [ ] **CLI Tool**
  - Code generation for aggregates
  - Event migration scripts
  - Database initialization
  - Development server with hot reload

- [ ] **Admin Dashboard**
  - Event stream visualization
  - Aggregate state inspection
  - Saga execution monitoring
  - Dead letter queue management

- [ ] **VS Code Extension**
  - Syntax highlighting for sagas
  - Event schema validation
  - Aggregate visualization
  - Test generation

### Testing & Quality
- [ ] **Contract Testing**
  - Event schema contract tests
  - Command/query contract validation
  - Producer/consumer contract testing

- [ ] **Chaos Engineering**
  - Random event store failures
  - Network partition simulation
  - Clock skew testing
  - Byzantine failure scenarios

- [ ] **Load Testing Framework**
  - Built-in load generation
  - Realistic event patterns
  - Bottleneck identification
  - Scalability reports

### Observability
- [ ] **Structured Logging**
  - OpenTelemetry logging integration
  - Correlation ID propagation
  - Log aggregation support (ELK, Loki)

- [ ] **Distributed Tracing**
  - Trace context propagation across sagas
  - Integration with AWS X-Ray
  - Integration with Azure Application Insights

- [ ] **Custom Metrics Backend**
  - StatsD support
  - InfluxDB integration
  - Datadog metrics

### Security
- [ ] **Audit Log**
  - Immutable audit trail
  - Command authorization tracking
  - GDPR compliance helpers (right to be forgotten)

- [ ] **Authentication/Authorization**
  - JWT token validation
  - Role-based access control (RBAC)
  - Attribute-based access control (ABAC)
  - Integration with Auth0, Keycloak

### Documentation & Examples
- [ ] **Real-World Examples**
  - E-commerce system (orders, payments, inventory)
  - Banking application (accounts, transactions)
  - Social media platform (posts, comments, likes)
  - IoT data pipeline (sensors, aggregations)

- [ ] **Migration Guides**
  - From traditional CRUD to Event Sourcing
  - From other ES frameworks (Axon, EventStore)
  - Database migration strategies

- [ ] **Video Tutorials**
  - Getting started series
  - Advanced patterns deep-dives
  - Performance optimization tips

### Ecosystem
- [ ] **FastAPI Integration**
  - Ready-to-use FastAPI routers
  - OpenAPI schema generation
  - WebSocket event streaming

- [ ] **Django Integration**
  - Django ORM projection backend
  - Management commands
  - Django REST framework serializers

- [ ] **Flask Integration**
  - Flask blueprints for CQRS
  - SQLAlchemy projection backend

- [ ] **Celery Integration**
  - Celery task as command handler
  - Background saga execution
  - Retry with exponential backoff

---

## Community & Growth

- [ ] **Blog Posts**
  - Event Sourcing explained
  - CQRS patterns
  - Saga choreography vs orchestration
  - When (not) to use Event Sourcing

- [ ] **Conference Talks**
  - PyCon proposals
  - EuroPython talks
  - Domain-Driven Design meetups

- [ ] **Benchmark Comparisons**
  - vs. Axon Framework (Java)
  - vs. EventStoreDB
  - vs. Marten (C#)
  - Performance characteristics

---

## Questions for the Community

1. **Integration Services**: Which cloud providers should we prioritize?
   - Google Cloud (BigQuery, Pub/Sub, Cloud SQL)
   - AWS (DynamoDB, SQS, Lambda)
   - Azure (Cosmos DB, Service Bus, Functions)

2. **Opinionated vs. Flexible**: Should we ship with batteries included or stay minimal?

3. **Licensing**: Should commercial features (e.g., enterprise monitoring) have dual licensing?

4. **Target Audience**: Startups, enterprises, or both?

---

**Last Updated:** 2026-01-04

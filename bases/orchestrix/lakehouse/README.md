# Lakehouse Platform Examples

This directory contains production-ready examples for building a data lakehouse platform with event sourcing, GDPR compliance, and data anonymization.

## Examples Overview

### 1. Data Anonymization (`example.py`)
Production-ready workflow for anonymizing sensitive data in a lakehouse platform.

**Features:**
- 8 anonymization strategies (masking, hashing, tokenization, generalization, etc.)
- Automatic dry-run validation
- Backup & rollback capabilities
- Full audit trail for compliance

**Run:**
```bash
uv run python -m examples.lakehouse.example
```

### 2. GDPR Compliance (`gdpr_simple.py`)
Complete GDPR-compliant data lake with right-to-be-forgotten implementation.

**Features:**
- Compliance level management (Standard, GDPR, Strict)
- Right-to-be-forgotten with 30-day deadlines
- PII tracking and validation
- Access audit logging

**Run:**
```bash
uv run python examples/lakehouse/gdpr_simple.py
```

### 3. Advanced GDPR Implementation (`gdpr.py`)
Full production implementation with aggregate pattern, commands, and events.

## Key Concepts

### Event Sourcing
All changes captured as immutable events.

### Aggregate Pattern
Domain logic encapsulated in aggregates.

### Compliance by Design
GDPR requirements built into the domain model.

## Architecture

```
Command → Aggregate → Event → Event Store
                ↓
           State Update
                ↓
         Query Functions
```

## Files

- `models.py` - Domain model (Commands, Events, Enums)
- `aggregate.py` - Aggregate root with business logic
- `engine.py` - Anonymization engine with strategies
- `handlers.py` - Command/Event handlers
- `saga.py` - Workflow orchestration
- `example.py` - Complete anonymization example
- `gdpr.py` - Full GDPR implementation
- `gdpr_simple.py` - Simple GDPR demo

## Documentation

See `docs/mkdocs/examples/` for detailed guides.

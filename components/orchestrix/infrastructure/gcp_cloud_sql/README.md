# Google Cloud SQL (PostgreSQL) Event Store for Orchestrix

This component provides an Event Store backend for Orchestrix using Google Cloud SQL (managed PostgreSQL).

## Features
- ACID-compliant event storage
- Atomic appends and strong consistency
- Flexible queries (by stream, type, time, ...)
- Managed backups, HA, and scaling via Google Cloud

## Configuration (.env example)
```
GCP_SQL_HOST=your-cloudsql-host
GCP_SQL_PORT=5432
GCP_SQL_DB=orchestrix
GCP_SQL_USER=orchestrix
GCP_SQL_PASSWORD=your-password
GCP_SQL_SSLMODE=require
```

## Usage
- Use as drop-in replacement for any EventStore Protocol implementation
- See `store.py` for API and integration details

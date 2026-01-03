-- ========================================
-- Orchestrix PostgreSQL Event Store Schema
-- ========================================
-- Version: 001
-- Description: Initial schema for event sourcing with snapshots
-- Author: Orchestrix Team
-- Date: 2024-01-15
--
-- Usage:
--   Apply: psql -U postgres -d orchestrix -f 001_postgres_schema.sql
--   Rollback: psql -U postgres -d orchestrix -f 001_postgres_schema_rollback.sql
-- ========================================

-- ========================================
-- Events Table
-- ========================================
-- Stores all domain events with CloudEvents metadata
-- Optimistic concurrency via UNIQUE constraint on (aggregate_id, version)

CREATE TABLE IF NOT EXISTS events (
    -- Internal row ID (auto-increment)
    id BIGSERIAL PRIMARY KEY,

    -- Event Sourcing fields
    aggregate_id TEXT NOT NULL,
    version INTEGER NOT NULL,

    -- CloudEvents Standard fields
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    event_source TEXT NOT NULL,
    event_subject TEXT,
    event_data JSONB NOT NULL,
    event_time TIMESTAMP WITH TIME ZONE NOT NULL,
    spec_version TEXT,
    data_content_type TEXT,
    data_schema TEXT,

    -- Orchestrix extensions
    correlation_id TEXT,
    causation_id TEXT,

    -- Audit timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure no version conflicts for same aggregate
    CONSTRAINT events_aggregate_version_unique UNIQUE (aggregate_id, version)
);

-- ========================================
-- Performance Indexes
-- ========================================

-- Index for loading events by aggregate (most common query)
CREATE INDEX IF NOT EXISTS idx_events_aggregate_id ON events (aggregate_id);

-- Index for filtering by event type (useful for projections)
CREATE INDEX IF NOT EXISTS idx_events_type ON events (event_type);

-- Index for temporal queries (newest events first)
CREATE INDEX IF NOT EXISTS idx_events_time ON events (event_time DESC);

-- Partial index for correlation tracking (only when correlation_id is set)
CREATE INDEX IF NOT EXISTS idx_events_correlation ON events (correlation_id) WHERE correlation_id IS NOT NULL;

-- Index for causation tracking
CREATE INDEX IF NOT EXISTS idx_events_causation ON events (causation_id) WHERE causation_id IS NOT NULL;

-- ========================================
-- Snapshots Table
-- ========================================
-- Stores aggregate snapshots for performance optimization
-- Only latest snapshot per aggregate is kept (upsert pattern)

CREATE TABLE IF NOT EXISTS snapshots (
    -- Composite primary key
    aggregate_id TEXT PRIMARY KEY,

    -- Snapshot metadata
    version INTEGER NOT NULL,
    snapshot_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for snapshot version queries
CREATE INDEX IF NOT EXISTS idx_snapshots_version ON snapshots (version);

-- ========================================
-- Comments (Documentation)
-- ========================================

COMMENT ON TABLE events IS 'Event store table: immutable log of all domain events';
COMMENT ON TABLE snapshots IS 'Snapshot store table: latest state snapshots for performance';

COMMENT ON COLUMN events.aggregate_id IS 'Unique identifier for the aggregate (e.g., order-123)';
COMMENT ON COLUMN events.version IS 'Monotonic version number starting at 1';
COMMENT ON COLUMN events.event_id IS 'Globally unique event identifier (UUID)';
COMMENT ON COLUMN events.event_type IS 'CloudEvents type (e.g., com.example.OrderCreated)';
COMMENT ON COLUMN events.event_source IS 'CloudEvents source (e.g., /orders/service)';
COMMENT ON COLUMN events.event_data IS 'Event payload as JSONB for flexible querying';
COMMENT ON COLUMN events.correlation_id IS 'Trace ID for distributed tracing';
COMMENT ON COLUMN events.causation_id IS 'ID of the command/event that caused this event';

COMMENT ON CONSTRAINT events_aggregate_version_unique ON events IS 'Ensures optimistic concurrency: prevents duplicate versions for same aggregate';

-- ========================================
-- Verification Queries
-- ========================================
-- Run these after applying the migration to verify schema

-- Check table structure
-- SELECT column_name, data_type, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'events'
-- ORDER BY ordinal_position;

-- Check indexes
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'events'
-- ORDER BY indexname;

-- ========================================
-- Rollback Script (001_postgres_schema_rollback.sql)
-- ========================================
-- DROP INDEX IF EXISTS idx_events_causation;
-- DROP INDEX IF EXISTS idx_events_correlation;
-- DROP INDEX IF EXISTS idx_events_time;
-- DROP INDEX IF EXISTS idx_events_type;
-- DROP INDEX IF EXISTS idx_events_aggregate_id;
-- DROP INDEX IF EXISTS idx_snapshots_version;
-- DROP TABLE IF EXISTS snapshots;
-- DROP TABLE IF EXISTS events;

-- ========================================
-- End of Migration
-- ========================================

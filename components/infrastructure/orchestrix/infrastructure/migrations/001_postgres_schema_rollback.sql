-- ========================================
-- Orchestrix PostgreSQL Event Store Schema
-- ========================================
-- Version: 001
-- Operation: ROLLBACK
-- Description: Remove event sourcing schema
-- Author: Orchestrix Team
-- Date: 2024-01-15
--
-- WARNING: This will permanently delete all events and snapshots!
--
-- Usage:
--   psql -U postgres -d orchestrix -f 001_postgres_schema_rollback.sql
-- ========================================

-- Drop indexes first
DROP INDEX IF EXISTS idx_events_causation;
DROP INDEX IF EXISTS idx_events_correlation;
DROP INDEX IF EXISTS idx_events_time;
DROP INDEX IF EXISTS idx_events_type;
DROP INDEX IF EXISTS idx_events_aggregate_id;
DROP INDEX IF EXISTS idx_snapshots_version;

-- Drop tables
DROP TABLE IF EXISTS snapshots;
DROP TABLE IF EXISTS events;

-- ========================================
-- End of Rollback
-- ========================================

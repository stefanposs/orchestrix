-- Beispiel-Schema für Events in BigQuery
CREATE TABLE IF NOT EXISTS orchestrix_events (
  event_id STRING NOT NULL,
  stream STRING NOT NULL,
  version INT64 NOT NULL,
  type STRING NOT NULL,
  data STRING NOT NULL, -- JSON-String
  timestamp TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stream_version ON orchestrix_events(stream, version);

-- One row per ingestion run (scheduled or manual). Safe to run more than once.

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id SERIAL PRIMARY KEY,
    market VARCHAR(20) NOT NULL,
    trigger VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    inserted INTEGER,
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_ingestion_runs_started
ON ingestion_runs(started_at DESC);

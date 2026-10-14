-- Which Country tabs a job appears under: canada, usa, north-america.
-- Safe to run more than once.

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS markets TEXT[] NOT NULL DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_jobs_markets
ON jobs USING GIN (markets);

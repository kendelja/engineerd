-- Work model (Remote / Hybrid / On-site) and detail-page enrichment
-- bookkeeping. Safe to run more than once.

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS work_model VARCHAR(20);

-- Set when the job's detail page was read and analysed.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS detail_checked_at TIMESTAMP;

-- Failed detail-page fetches, so dead links are not retried forever.
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS detail_attempts SMALLINT NOT NULL DEFAULT 0;

-- remote_type was never populated by the old normalizer (always false).
UPDATE jobs SET remote_type = NULL WHERE work_model IS NULL;

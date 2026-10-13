-- Adds the junior-fit analysis columns.
-- Safe to run more than once.

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS years_required SMALLINT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS years_evidence TEXT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS skills TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS fit_score SMALLINT;
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS fit_label VARCHAR(20);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS fit_reasons TEXT[] NOT NULL DEFAULT '{}';
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS fit_confidence VARCHAR(10);

CREATE INDEX IF NOT EXISTS idx_jobs_fit_label
ON jobs(fit_label);

CREATE INDEX IF NOT EXISTS idx_jobs_skills
ON jobs USING GIN (skills);

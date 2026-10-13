CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,

    source VARCHAR(100) NOT NULL,
    source_job_id VARCHAR(255),

    title TEXT NOT NULL,
    company TEXT NOT NULL,
    company_logo TEXT,
    location TEXT,

    description TEXT,
    url TEXT NOT NULL,

    posted_at TIMESTAMP,
    discovered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    experience_level VARCHAR(100),
    employment_type VARCHAR(100),
    remote_type boolean,
    work_model VARCHAR(20),

    salary_min NUMERIC,
    salary_max NUMERIC,
    salary_period VARCHAR(20),

    -- Junior-fit analysis (see Backend/app/ingestion/analyzer.py)
    years_required SMALLINT,
    years_evidence TEXT,
    skills TEXT[] NOT NULL DEFAULT '{}',
    fit_score SMALLINT,
    fit_label VARCHAR(20),
    fit_reasons TEXT[] NOT NULL DEFAULT '{}',
    fit_confidence VARCHAR(10),

    -- Detail-page enrichment bookkeeping
    detail_checked_at TIMESTAMP,
    detail_attempts SMALLINT NOT NULL DEFAULT 0,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(source, source_job_id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_posted_at
ON jobs(posted_at);

CREATE INDEX IF NOT EXISTS idx_jobs_source
ON jobs(source);

CREATE INDEX IF NOT EXISTS idx_jobs_title
ON jobs(title);

CREATE INDEX IF NOT EXISTS idx_jobs_fit_label
ON jobs(fit_label);

CREATE INDEX IF NOT EXISTS idx_jobs_skills
ON jobs USING GIN (skills);
-- Ingestion run log (see migrations/003_ingestion_runs.sql)
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

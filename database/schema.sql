
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id UUID PRIMARY KEY,
    pipeline_name VARCHAR(150) NOT NULL DEFAULT 'orders_pipeline',
    status VARCHAR(20) NOT NULL DEFAULT 'RUNNING'
        CHECK (status IN ('RUNNING', 'SUCCESS', 'FAILED')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    duration_seconds DOUBLE PRECISION,
    bronze_records INTEGER NOT NULL DEFAULT 0,
    silver_records INTEGER NOT NULL DEFAULT 0,
    quarantine_records INTEGER NOT NULL DEFAULT 0,
    total_checks INTEGER NOT NULL DEFAULT 0,
    passed_checks INTEGER NOT NULL DEFAULT 0,
    failed_checks INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    trigger_source VARCHAR(50) NOT NULL DEFAULT 'api',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT valid_run_duration
        CHECK (duration_seconds IS NULL OR duration_seconds >= 0),

    CONSTRAINT valid_run_counts
        CHECK (
            bronze_records >= 0
            AND silver_records >= 0
            AND quarantine_records >= 0
            AND total_checks >= 0
            AND passed_checks >= 0
            AND failed_checks >= 0
        )
);

CREATE TABLE IF NOT EXISTS pipeline_run_quality_results (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES pipeline_runs(run_id)
        ON DELETE CASCADE,
    dataset VARCHAR(150),
    check_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('PASS', 'FAIL', 'UNKNOWN')),
    failed_records INTEGER NOT NULL DEFAULT 0
        CHECK (failed_records >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (run_id, check_name)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started_at
    ON pipeline_runs (started_at DESC);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status
    ON pipeline_runs (status);

CREATE INDEX IF NOT EXISTS idx_run_quality_run_id
    ON pipeline_run_quality_results (run_id);

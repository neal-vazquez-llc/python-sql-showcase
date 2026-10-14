-- SQLite demonstration schema; not a production schema export.
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,
    request_key TEXT UNIQUE NOT NULL,
    payload TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('queued','running','succeeded','failed')),
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
    generation INTEGER NOT NULL DEFAULT 0,
    owner TEXT,
    lease_until REAL,
    created_at REAL NOT NULL,
    CHECK ((state = 'running' AND owner IS NOT NULL AND lease_until IS NOT NULL)
        OR (state <> 'running' AND owner IS NULL AND lease_until IS NULL))
);
CREATE INDEX jobs_available ON jobs(state, created_at, id);
CREATE TABLE results (
    job_id TEXT PRIMARY KEY REFERENCES jobs(id),
    result_json TEXT NOT NULL
);

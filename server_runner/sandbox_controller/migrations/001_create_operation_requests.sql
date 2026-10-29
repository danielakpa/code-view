-- Store sandbox operation request IDs.
-- PostgreSQL uses the primary key to reject duplicates.

CREATE TABLE IF NOT EXISTS runner.sandbox_operation_requests (

    -- Unique ID generated for each operation request.
    request_id UUID PRIMARY KEY,

    -- Sandbox associated with the operation.
    sandbox_id UUID NOT NULL,

    -- Developer and group associated with the request.
    developer_id BIGINT NOT NULL CHECK (developer_id > 0),
    group_id BIGINT NOT NULL CHECK (group_id > 0),

    -- Operation requested by the Runner.
    operation VARCHAR(20) NOT NULL
        CHECK (operation IN ('create', 'start', 'stop', 'inspect')),

    -- Time the request ID was claimed.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Support queries involving a particular sandbox.
CREATE INDEX IF NOT EXISTS idx_sandbox_operation_requests_sandbox
ON runner.sandbox_operation_requests (sandbox_id);
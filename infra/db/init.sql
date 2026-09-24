-- MAX Platform PostgreSQL Database Initialization Script
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant schema privileges
GRANT ALL PRIVILEGES ON DATABASE maxdb TO max;

-- Audit table schema stub for Module 33 compatibility
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(64) NOT NULL,
    actor VARCHAR(128) NOT NULL,
    action VARCHAR(128) NOT NULL,
    resource VARCHAR(256) NOT NULL,
    status VARCHAR(32) NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);

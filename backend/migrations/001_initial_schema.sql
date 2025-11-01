-- Initial schema for OpenAI Assistant orchestrator
-- Run with: psql -U opa -d opa -f 001_initial_schema.sql

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- For text search optimization

-- Create enum types
CREATE TYPE job_status AS ENUM ('pending', 'running', 'completed', 'failed', 'cancelled');
CREATE TYPE execution_mode AS ENUM ('flow', 'mcp', 'agent', 'auto');

-- Memory items table with vector embeddings
CREATE TABLE IF NOT EXISTS memory_items (
    id VARCHAR(64) PRIMARY KEY,  -- SHA256 hash for idempotency
    text TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    speaker_id VARCHAR(255),
    embedding VECTOR(384)  -- sentence-transformers/all-MiniLM-L6-v2
);

-- Indexes for memory_items
CREATE INDEX idx_memory_items_tags ON memory_items USING GIN(tags);
CREATE INDEX idx_memory_items_created_at ON memory_items(created_at DESC);
CREATE INDEX idx_memory_items_embedding ON memory_items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_memory_items_text_trgm ON memory_items USING GIN(text gin_trgm_ops);

-- Jobs table for orchestrator tracking
CREATE TABLE IF NOT EXISTS jobs (
    id VARCHAR(64) PRIMARY KEY,  -- SHA256 hash for idempotency
    intent VARCHAR(255) NOT NULL,
    mode execution_mode NOT NULL,
    status job_status NOT NULL DEFAULT 'pending',
    inputs JSONB NOT NULL,
    result JSONB,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    callback_url TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Indexes for jobs
CREATE INDEX idx_jobs_intent ON jobs(intent);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_completed_at ON jobs(completed_at DESC) WHERE completed_at IS NOT NULL;

-- Trigger to auto-update updated_at on memory_items
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_memory_items_updated_at
    BEFORE UPDATE ON memory_items
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE memory_items IS 'Stores user memories with vector embeddings for semantic search';
COMMENT ON TABLE jobs IS 'Tracks orchestrator job execution with idempotency';
COMMENT ON COLUMN memory_items.id IS 'SHA256 hash of text+tags for deduplication';
COMMENT ON COLUMN memory_items.embedding IS 'Vector embedding from all-MiniLM-L6-v2 (384 dimensions)';
COMMENT ON COLUMN jobs.id IS 'SHA256 hash of intent+inputs for idempotency';
COMMENT ON COLUMN jobs.metadata IS 'Additional context (user_id, trace_id, etc.)';

-- RAGVersion Supabase Schema Migration
-- Run this in your Supabase SQL Editor to create the required tables

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Documents table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version_count INTEGER DEFAULT 1,
    current_version INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Versions table
CREATE TABLE IF NOT EXISTS versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    file_size BIGINT NOT NULL,
    change_type TEXT NOT NULL CHECK (change_type IN ('created', 'modified', 'deleted', 'restored')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(document_id, version_number)
);

-- Content snapshots table
CREATE TABLE IF NOT EXISTS content_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    version_id UUID NOT NULL REFERENCES versions(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    compressed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(version_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path);
CREATE INDEX IF NOT EXISTS idx_documents_updated_at ON documents(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);
CREATE INDEX IF NOT EXISTS idx_documents_metadata ON documents USING GIN(metadata);

CREATE INDEX IF NOT EXISTS idx_versions_document_id ON versions(document_id);
CREATE INDEX IF NOT EXISTS idx_versions_version_number ON versions(document_id, version_number DESC);
CREATE INDEX IF NOT EXISTS idx_versions_created_at ON versions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_versions_content_hash ON versions(content_hash);

CREATE INDEX IF NOT EXISTS idx_content_version_id ON content_snapshots(version_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Enable Row Level Security (RLS)
-- Uncomment if you want to enable RLS for multi-tenant scenarios
-- ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE versions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE content_snapshots ENABLE ROW LEVEL SECURITY;

-- Optional: Create RLS policies
-- Example: Allow all operations for service role
-- CREATE POLICY "Service role can do everything on documents"
--     ON documents
--     FOR ALL
--     TO service_role
--     USING (true)
--     WITH CHECK (true);

COMMENT ON TABLE documents IS 'Tracks all documents in the RAG system';
COMMENT ON TABLE versions IS 'Stores version history for each document';
COMMENT ON TABLE content_snapshots IS 'Stores the actual content for each version (optionally compressed)';

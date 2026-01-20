-- RAGVersion Chunk-Level Versioning Migration (v0.10.0)
-- This migration adds chunk-level tracking for cost-optimized RAG operations

-- =============================================================================
-- SUPABASE / POSTGRESQL VERSION
-- =============================================================================
-- Run this section in your Supabase SQL Editor

-- Chunks table
CREATE TABLE IF NOT EXISTS chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_id UUID NOT NULL REFERENCES versions(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(version_id, chunk_index)
);

-- Chunk content table (separate for compression support)
CREATE TABLE IF NOT EXISTS chunk_content (
    chunk_id UUID PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    compressed BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Performance indexes for chunks
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_version_id ON chunks(version_id);
CREATE INDEX IF NOT EXISTS idx_chunks_content_hash ON chunks(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_version ON chunks(document_id, version_id);
CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING GIN(metadata);

-- Index for chunk content
CREATE INDEX IF NOT EXISTS idx_chunk_content_chunk_id ON chunk_content(chunk_id);

-- Comments for documentation
COMMENT ON TABLE chunks IS 'Tracks content chunks within document versions for cost-optimized embedding updates';
COMMENT ON TABLE chunk_content IS 'Stores actual chunk content with optional compression';
COMMENT ON COLUMN chunks.chunk_index IS '0-indexed position of chunk within document';
COMMENT ON COLUMN chunks.content_hash IS 'SHA-256 hash for change detection';
COMMENT ON COLUMN chunks.token_count IS 'Token count for cost tracking';


-- =============================================================================
-- SQLITE VERSION
-- =============================================================================
-- This section is automatically executed by SQLiteStorage._create_tables()
-- Included here for reference and manual SQLite database creation

-- Note: SQLite differences from PostgreSQL:
-- 1. Uses TEXT for UUIDs instead of UUID type
-- 2. Uses INTEGER for BOOLEAN (0=false, 1=true)
-- 3. Uses TEXT for timestamps (ISO format)
-- 4. JSONB -> TEXT (stores JSON as string)
-- 5. No DEFAULT uuid_generate_v4() - handled in Python code

/*
-- Chunks table (SQLite)
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_id TEXT NOT NULL REFERENCES versions(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content_hash TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    UNIQUE(version_id, chunk_index)
);

-- Chunk content table (SQLite)
CREATE TABLE IF NOT EXISTS chunk_content (
    chunk_id TEXT PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    compressed INTEGER DEFAULT 1,
    created_at TEXT NOT NULL
);

-- Performance indexes (SQLite)
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_version_id ON chunks(version_id);
CREATE INDEX IF NOT EXISTS idx_chunks_content_hash ON chunks(content_hash);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_version ON chunks(document_id, version_id);

CREATE INDEX IF NOT EXISTS idx_chunk_content_chunk_id ON chunk_content(chunk_id);
*/


-- =============================================================================
-- MIGRATION VERIFICATION QUERIES
-- =============================================================================

-- Check if migration was successful
-- SELECT COUNT(*) as chunks_table_exists FROM information_schema.tables WHERE table_name = 'chunks';
-- SELECT COUNT(*) as chunk_content_table_exists FROM information_schema.tables WHERE table_name = 'chunk_content';

-- Verify indexes
-- SELECT indexname FROM pg_indexes WHERE tablename IN ('chunks', 'chunk_content');

-- Sample query: Get chunks for a specific version
-- SELECT c.*, cc.content
-- FROM chunks c
-- LEFT JOIN chunk_content cc ON c.id = cc.chunk_id
-- WHERE c.version_id = 'YOUR_VERSION_ID'
-- ORDER BY c.chunk_index;

-- Sample query: Calculate embedding cost savings for a document
-- SELECT
--     d.file_name,
--     COUNT(DISTINCT c.id) as total_chunks,
--     COUNT(DISTINCT c.content_hash) as unique_chunks,
--     ROUND((1 - COUNT(DISTINCT c.content_hash)::decimal / COUNT(DISTINCT c.id)) * 100, 2) as deduplication_percentage
-- FROM documents d
-- JOIN versions v ON d.id = v.document_id
-- JOIN chunks c ON v.id = c.version_id
-- GROUP BY d.id, d.file_name;

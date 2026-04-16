-- NEXUS pgvector migration — run on Supabase (local or hosted)
-- Creates the document_chunks table and the similarity search function.

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Document chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id TEXT PRIMARY KEY,
    document_name TEXT NOT NULL,
    page_number INTEGER NOT NULL DEFAULT 1,
    content TEXT NOT NULL,
    section_header TEXT DEFAULT '',
    source_path TEXT DEFAULT '',
    ingestion_date TIMESTAMPTZ DEFAULT NOW(),
    content_hash TEXT NOT NULL,
    embedding VECTOR(384),  -- all-MiniLM-L6-v2 = 384 dimensions
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast similarity search
CREATE INDEX IF NOT EXISTS idx_chunks_embedding
ON document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index for document lookups
CREATE INDEX IF NOT EXISTS idx_chunks_document_name
ON document_chunks (document_name);

-- Index for content hash (deduplication)
CREATE UNIQUE INDEX IF NOT EXISTS idx_chunks_content_hash
ON document_chunks (content_hash);

-- Similarity search RPC function
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding VECTOR(384),
    match_count INTEGER DEFAULT 12
)
RETURNS TABLE (
    id TEXT,
    document_name TEXT,
    page_number INTEGER,
    content TEXT,
    section_header TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_name,
        dc.page_number,
        dc.content,
        dc.section_header,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Run this in your Supabase SQL editor before starting the backend

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Main chunks table
CREATE TABLE IF NOT EXISTS document_chunks (
    id          UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    document_name TEXT NOT NULL,
    page_number  INT  NOT NULL DEFAULT 1,
    content      TEXT NOT NULL,
    embedding    vector(384),
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx
    ON document_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- RPC function used by similarity_search()
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding vector(384),
    match_count     INT DEFAULT 12
)
RETURNS TABLE (
    id            UUID,
    document_name TEXT,
    page_number   INT,
    content       TEXT,
    similarity    FLOAT
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
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

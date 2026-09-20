-- Enable pgvector extension for Supabase Vector Storage
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Ingested Documents Table
CREATE TABLE IF NOT EXISTS public.documents (
    file_id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    gdrive_url TEXT,
    modified_time TEXT,
    md5_checksum TEXT,
    pages_count INTEGER DEFAULT 0,
    elements_count INTEGER DEFAULT 0,
    chunks_count INTEGER DEFAULT 0,
    ingested_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'indexed'
);

-- 2. Document Vector Chunks Table (with pgvector HNSW index)
CREATE TABLE IF NOT EXISTS public.document_chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES public.documents(file_id) ON DELETE CASCADE,
    file_id TEXT NOT NULL,
    file_name TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    section TEXT,
    element_type TEXT NOT NULL,
    content TEXT NOT NULL,
    parent_element_id TEXT,
    gdrive_url TEXT,
    image_path TEXT,
    embedding vector(384), -- 384 dimensions for all-MiniLM-L6-v2 embeddings
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW Vector Index for ultra-fast Cosine Distance Search in Supabase
CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx 
ON public.document_chunks 
USING hnsw (embedding vector_cosine_ops);

-- 3. Ingestion Jobs Table
CREATE TABLE IF NOT EXISTS public.ingestion_jobs (
    job_id TEXT PRIMARY KEY,
    status TEXT NOT NULL, -- 'processing', 'completed', 'completed_with_errors', 'failed'
    progress_percentage REAL DEFAULT 0.0,
    files_total INTEGER DEFAULT 0,
    files_processed INTEGER DEFAULT 0,
    files_failed INTEGER DEFAULT 0,
    errors_json JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Customer Support Tickets Table
CREATE TABLE IF NOT EXISTS public.tickets (
    ticket_id TEXT PRIMARY KEY,
    channel TEXT NOT NULL, -- 'email', 'chat', 'api_docs', 'forum'
    customer_name TEXT NOT NULL,
    customer_tier TEXT DEFAULT 'Standard',
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    urgency TEXT DEFAULT 'medium',
    status TEXT DEFAULT 'pending_review', -- 'pending_review', 'approved', 'escalated'
    ai_draft JSONB,
    confidence_score REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Decision & Governance Audit Logs Table
CREATE TABLE IF NOT EXISTS public.decision_logs (
    log_id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    ticket_id TEXT NOT NULL,
    intent TEXT,
    confidence_score REAL,
    guardrail_passed BOOLEAN,
    guardrail_reason TEXT,
    action_taken TEXT NOT NULL, -- 'auto_replied', 'copilot_approved', 'escalated_tier2'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vector Similarity Search RPC Function for Supabase
CREATE OR REPLACE FUNCTION match_document_chunks (
  query_embedding vector(384),
  match_threshold float,
  match_count int,
  filter_file_id text DEFAULT NULL
)
RETURNS TABLE (
  chunk_id text,
  document_id text,
  file_id text,
  file_name text,
  page_number int,
  section text,
  element_type text,
  content text,
  parent_element_id text,
  gdrive_url text,
  image_path text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.chunk_id,
    dc.document_id,
    dc.file_id,
    dc.file_name,
    dc.page_number,
    dc.section,
    dc.element_type,
    dc.content,
    dc.parent_element_id,
    dc.gdrive_url,
    dc.image_path,
    1 - (dc.embedding <=> query_embedding) AS similarity
  FROM public.document_chunks dc
  WHERE 
    (filter_file_id IS NULL OR dc.file_id = filter_file_id)
    AND (1 - (dc.embedding <=> query_embedding)) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

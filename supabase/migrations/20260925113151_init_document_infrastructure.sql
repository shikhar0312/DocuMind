-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Documents Table
CREATE TABLE documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    file_path TEXT NOT NULL, -- Format: [user_id]/[document_id].[ext]
    file_type TEXT NOT NULL, -- e.g., 'application/pdf', 'text/plain'
    size_bytes BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 2. Chats Table
CREATE TABLE chats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 3. Document Chunks Table (for Embeddings)
CREATE TABLE document_chunks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR, -- Dimension deferred until embedding model is finalized
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_chats_document_id ON chats(document_id);
CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);

-- Enable RLS on all tables
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Documents Policies
CREATE POLICY "Users can insert their own documents" ON documents FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can view their own documents" ON documents FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update their own documents" ON documents FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own documents" ON documents FOR DELETE USING (auth.uid() = user_id);

-- Chats Policies
CREATE POLICY "Users can insert their own chats" ON chats FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can view their own chats" ON chats FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update their own chats" ON chats FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete their own chats" ON chats FOR DELETE USING (auth.uid() = user_id);

-- Document Chunks Policies
CREATE POLICY "Users can insert chunks for their documents" ON document_chunks FOR INSERT WITH CHECK (
    EXISTS (SELECT 1 FROM documents WHERE id = document_chunks.document_id AND user_id = auth.uid())
);
CREATE POLICY "Users can view chunks of their documents" ON document_chunks FOR SELECT USING (
    EXISTS (SELECT 1 FROM documents WHERE id = document_chunks.document_id AND user_id = auth.uid())
);
CREATE POLICY "Users can delete chunks of their documents" ON document_chunks FOR DELETE USING (
    EXISTS (SELECT 1 FROM documents WHERE id = document_chunks.document_id AND user_id = auth.uid())
);

-- Create the private bucket with explicit file constraints (20MB limit, PDF/TXT only)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types) 
VALUES (
    'documents', 
    'documents', 
    false, 
    20971520, 
    ARRAY['application/pdf', 'text/plain']::text[]
) 
ON CONFLICT (id) DO UPDATE SET 
    public = false,
    file_size_limit = 20971520,
    allowed_mime_types = ARRAY['application/pdf', 'text/plain']::text[];

-- (RLS is already enabled on storage.objects by default)

-- Storage Policies
-- 1. Users can upload files to their own folder path: [user_id]/[file]
CREATE POLICY "Users can upload their own documents" ON storage.objects FOR INSERT TO authenticated WITH CHECK (
    bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text
);

-- 2. Users can read files in their own folder
CREATE POLICY "Users can view their own documents" ON storage.objects FOR SELECT TO authenticated USING (
    bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text
);

-- 3. Users can delete files in their own folder
CREATE POLICY "Users can delete their own documents" ON storage.objects FOR DELETE TO authenticated USING (
    bucket_id = 'documents' AND (storage.foldername(name))[1] = auth.uid()::text
);

-- 1. Add status and error_message to documents
ALTER TABLE documents ADD COLUMN status TEXT DEFAULT 'processing' NOT NULL;
ALTER TABLE documents ADD COLUMN error_message TEXT;

-- 2. Add page_number and user_id to document_chunks
ALTER TABLE document_chunks ADD COLUMN page_number INTEGER;
ALTER TABLE document_chunks ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE;

-- Update existing document_chunks to have the correct user_id (if any exist)
UPDATE document_chunks
SET user_id = documents.user_id
FROM documents
WHERE document_chunks.document_id = documents.id;

-- Now make user_id NOT NULL
ALTER TABLE document_chunks ALTER COLUMN user_id SET NOT NULL;

-- 3. Set the embedding vector dimension to 768 (for Gemini text-embedding-004)
ALTER TABLE document_chunks ALTER COLUMN embedding TYPE VECTOR(768);

-- 4. Update Document Chunks Policies to use the direct user_id column for performance
DROP POLICY IF EXISTS "Users can insert chunks for their documents" ON document_chunks;
DROP POLICY IF EXISTS "Users can view chunks of their documents" ON document_chunks;
DROP POLICY IF EXISTS "Users can delete chunks of their documents" ON document_chunks;

CREATE POLICY "Users can insert chunks for their documents" ON document_chunks 
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view chunks of their documents" ON document_chunks 
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update chunks of their documents" ON document_chunks 
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete chunks of their documents" ON document_chunks 
    FOR DELETE USING (auth.uid() = user_id);

-- 5. Add an index to user_id on document_chunks for faster RLS and filtering
CREATE INDEX idx_document_chunks_user_id ON document_chunks(user_id);

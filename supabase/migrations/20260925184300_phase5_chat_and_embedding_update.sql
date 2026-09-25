-- 1. Safely mark existing completed documents for reprocessing
UPDATE documents 
SET status = 'processing', 
    error_message = 'Awaiting dimension upgrade (768 to 3072). Please wait for background reprocessing.' 
WHERE status = 'completed';

-- 2. Update embedding dimension to 3072 for gemini-embedding-001
TRUNCATE TABLE document_chunks;
ALTER TABLE document_chunks ALTER COLUMN embedding TYPE VECTOR(3072);

-- 3. Create messages table
CREATE TABLE messages (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    chat_id UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    sources JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- 4. Indexes for fast sequential message retrieval within a chat
CREATE INDEX idx_messages_chat_id_created_at ON messages(chat_id, created_at);

-- 5. Enable RLS
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- 6. RLS Policies for messages
CREATE POLICY "Users can manage messages in their own chats" ON messages
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM chats 
            WHERE id = messages.chat_id AND user_id = auth.uid()
        )
    ) WITH CHECK (
        EXISTS (
            SELECT 1 FROM chats 
            WHERE id = messages.chat_id AND user_id = auth.uid()
        )
    );

-- 7. RPC Function for Vector Search
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding VECTOR(3072),
    match_threshold FLOAT,
    match_count INT,
    p_document_id UUID,
    p_user_id UUID
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    user_id UUID,
    page_number INT,
    content TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.user_id,
        dc.page_number,
        dc.content,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    WHERE dc.document_id = p_document_id
      AND dc.user_id = p_user_id
      AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

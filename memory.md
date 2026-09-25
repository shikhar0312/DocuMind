# Memory — Phase 2: Database & Storage Infrastructure

Last updated: 2026-09-25

## What was built

- **Supabase CLI**: Initialized the local Supabase environment (`supabase/config.toml`).
- **Database Schema**: Created the primary infrastructure migration (`supabase/migrations/20260925113151_init_document_infrastructure.sql`) containing the `documents`, `chats`, and `document_chunks` tables.
- **Storage**: Created the private `documents` Supabase Storage bucket with strict constraints (20MB max file size, restricted to `application/pdf` and `text/plain`).
- **Row Level Security**: Applied strict RLS policies to all new tables and the storage bucket to guarantee user data isolation based on `auth.uid()`.

## Decisions made

- Included the `chats` table early to establish the strict one-to-one relationship between a chat and a document.
- Storage file paths strictly follow the pattern `[user_id]/[document_id].[ext]` to allow the storage RLS policy to efficiently check ownership.
- **Deferred Vector Dimensions**: Explicitly defined the embedding column as `VECTOR` without a strict dimension size (and without an HNSW index yet). This keeps the schema flexible until the exact Gemini embedding model is chosen in Phase 3.

## Problems solved

- Resolved a Supabase remote migration permission error (`SQLSTATE 42501`) by removing the redundant `ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY` statement, as Supabase already manages RLS natively for that internal table.

## Current state

- Phase 2 (Database and Storage Infrastructure) is 100% complete and successfully pushed to the remote Supabase project. The backend architecture is ready to store user files and relational data securely.

## Next session starts with

- **Phase 3: Document Upload Pipeline.** 
- Next steps: Implement the frontend UI for document upload and the backend FastAPI upload endpoints to interact with the newly deployed Supabase infrastructure.

## Open questions

- Which exact Gemini embedding model will be used in Phase 3? (We will need to lock this in before generating embeddings).

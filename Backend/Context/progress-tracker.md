# DocuMind — Progress Tracker

Use `[x]` only for work completed and verified or explicitly confirmed. Keep incomplete work as `[ ]`.

## Phase 1: Project Setup & Authentication
- [x] Create `DocuMind/Frontend`.
- [x] Create `Backend/Context` and `Backend/Design`.
- [x] Initialize React + Vite frontend scaffold (confirmed in user's VS Code screenshot).
- [x] Initialize backend with `uv` and create managed virtual environment.
- [x] Install initial FastAPI, Uvicorn, LangChain, Supabase, and PDF dependencies.
- [x] Create `Backend/app/main.py`.
- [x] Confirm FastAPI starts successfully at port 8000 (`Application startup complete` reported).
- [x] Generate five UI reference images: login, chat workspace, upload, document viewer, settings.
- [x] Add/review all context Markdown files in `Backend/Context/`.
- [x] Place five UI reference images in `Backend/Design/` with clear filenames.
- [x] Implement login page UI from reference (visual UI only).
- [x] Connect Google OAuth through Supabase Auth.
- [x] Implement chat workspace shell.
- [x] Confirm frontend and backend start reliably in separate terminals.

## Phase 2: Database & Storage Infrastructure
- [x] Finalize Supabase schema, vector dimensions/index, Storage bucket, and RLS policies.

## Phase 3: Document Upload Pipeline
- [x] Implement document upload page and states.
- [x] Implement authenticated document upload.

## Phase 4: RAG Processing & Embeddings
- [x] Finalize supported file formats and upload limits.
- [x] Select embedding model/provider.
- [x] Select answer-generation LLM/provider.
- [ ] Implement document text extraction and chunking.
- [ ] Generate and store embeddings.
- [ ] Implement semantic similarity search.

## Phase 5: Chat & Q&A Integration
- [ ] Define API contracts for auth, documents, chats, and Q&A.
- [ ] Implement chats and message persistence.
- [ ] Connect frontend to backend APIs.
- [ ] Implement document viewer page.
- [ ] Implement grounded answer generation with source references.
- [ ] Implement clear no-evidence responses.

## Phase 6: Polish & Quality Assurance
- [ ] Implement settings page.
- [ ] Verify responsive behavior and accessibility.
- [ ] Verify users cannot access other users' documents/chats.
- [ ] Run frontend build/type checks and backend tests.
- [ ] Test upload, processing failure, retrieval, answer, and empty states.

## Open Questions
- [x] Which embedding model/provider? -> **Gemini Embeddings**
- [x] Which LLM/provider for answer generation? -> **Google Gemini**
- [x] Which file formats in the first release (PDF only or more)? -> **PDF and TXT only**
- [x] Can a chat query one document or multiple documents? -> **One document per chat**
- [x] What upload size and per-user storage limits? -> **20MB max per file**
- [x] What exact Supabase tables, vector dimensions, indexes, and RLS policies? -> **documents, chats, document_chunks (vector dimension deferred), RLS enabled, Storage constrained to 20MB PDF/TXT**
- [x] Which frontend component library, if any? -> **Tailwind CSS with Custom Components**
- [ ] Is OCR for scanned PDFs required in the first release?

## Confirmed Architecture Decisions
- [x] Frontend: React + Vite + TypeScript.
- [x] Backend: FastAPI with `uv`.
- [x] RAG framework: LangChain.
- [x] Data platform: Supabase.
- [x] Planned vector storage/search: PostgreSQL + pgvector.
- [x] Original files: Supabase Storage.
- [x] Authentication plan: Supabase Auth + Google OAuth.
- [x] Visual direction: purple and soft white; ChatGPT-inspired sidebar/chat layout.
- [x] Embedding and LLM providers: Google Gemini + Gemini Embeddings.
- [x] UI Library: Custom components with Tailwind CSS.

## Session Notes
- Backend Uvicorn reported `Application startup complete` at port 8000.
- Initial ASGI app-attribute error disappeared after `app/main.py` was populated and the server reloaded.
- Frontend scaffold is present with `src`, `public`, and Vite files.
- Phase 1 Frontend UI (Login, Workspace Shell) and Auth Context implemented and successfully built.
- Supabase Database schema (`documents`, `chats`, `document_chunks`), Storage bucket (`documents`), and strict RLS policies have been successfully deployed. Ready for document upload implementation.

# DocuMind — Architecture

## Technology Stack

| Layer | Technology | Responsibility |
|---|---|---|
| Frontend | React, Vite, TypeScript | UI and client interactions |
| Backend | FastAPI (Python) | API, authorization, orchestration |
| Python environment | `uv` | Dependencies and virtual environment |
| RAG framework | LangChain | Loading, splitting, retrieval workflow |
| Database | Supabase PostgreSQL | Metadata, chats, chunks, vector records |
| Vector search | pgvector | Embedding storage and similarity search |
| File storage | Supabase Storage | Original uploaded files |
| Authentication | Supabase Auth + Google OAuth | User identity and sessions |
| Embedding / LLM | Not selected yet | Embeddings and answer generation |

## Project Boundaries
- `Frontend/`: React/Vite app; calls the backend API.
- `Backend/app/`: FastAPI code, business logic, retrieval, and persistence integration.
- `Backend/Context/`: project context and progress files.
- `Backend/Design/`: five UI reference images.
- Supabase Auth: Google identity and sessions.
- Supabase PostgreSQL + pgvector: structured data, chunks, embeddings, and vector search.
- Supabase Storage: original uploaded files.

## Planned Data Entities
- `documents`: owner ID, filename, storage path, metadata, processing status, timestamps.
- `document_chunks`: document ID, owner ID or securely derived ownership, chunk text, chunk order, page/source metadata, embedding.
- `chats`: owner ID, title, timestamps.
- `messages`: chat ID, role, content, timestamps, optional source references.

The exact schema, embedding dimensions, indexes, and retention rules are not finalized.

## Authentication and Access
- Users authenticate with Supabase Auth using Google.
- Backend validates the user's Supabase access token for protected operations.
- Every document, chunk, chat, and message must be scoped to its owner.
- Database policies must prevent cross-user access.
- Never expose Supabase service-role credentials in frontend code.
- Finalize the division of responsibility between RLS and backend authorization before protected features are implemented.

## Non-Negotiable Rules
- Do not present outside knowledge as if it came from a user's document.
- Retrieve only from documents the authenticated user can access.
- Similarity alone is not proof that evidence supports an answer.
- Preserve source metadata such as filename and page number when available.
- Keep original files separate from embeddings.
- Keep secrets in environment variables; never commit `.env`.
- Do not mark processing complete until required steps succeed.

# Memory — Transitioning to Phase 5: Document Viewer & Chat

Last updated: 2026-09-25 18:37:00

## What was built

- **Phase 4 Completion**: The asynchronous document pipeline (text extraction via `pypdf`, chunking via `RecursiveCharacterTextSplitter`, and Gemini `text-embedding-004` vector generation) is fully built, integrated with FastAPI `BackgroundTasks`, and storing data in Supabase `pgvector`.
- **Environment Configured**: The `GEMINI_API_KEY` was successfully added to the backend `.env` file and the pipeline is fully operational.
- **Frontend Status Polling**: The React app now correctly polls the backend to track document processing status before allowing the user to proceed.

## Decisions made

- No new implementation decisions made yet. 
- We are currently in the **Architectural Alignment** step for Phase 5.

## Problems solved

- Clarified environment variable placement (frontend vs. backend `.env`) to ensure the Gemini API key remains securely restricted to the backend server.

## Current state

- Phase 4 is officially complete and working.
- We have initiated Phase 5 (Document Viewer & Chat), starting with the `architect` skill to align on terminology ("Document Viewer", "Retrieval Chain", and "Chat Interface").

## Next session starts with

- **Phase 5 Planning Continuation**: The developer needs to confirm or correct the language alignment questions for Phase 5:
  1. Is the **Document Viewer** a side-by-side UI displaying the PDF/TXT file?
  2. Does the **Retrieval Chain** correctly describe embedding the query, searching pgvector, and generating an LLM response?
  3. Is the **Chat Interface** the standard messaging UI hitting a new FastAPI `/api/chats` endpoint?

## Open questions

- (From Phase 5 alignment) Do the defined terms accurately represent what we are about to build?
- Which PDF viewer library will we use for the frontend?
- What vector retrieval strategy (e.g., standard similarity, MMR, top-k) will be used in the LangChain logic?

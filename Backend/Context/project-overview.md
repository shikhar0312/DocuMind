# DocuMind — Project Overview

## Overview
DocuMind is a document question-answering web application. Users sign in, upload documents, and ask questions about their contents. The system retrieves relevant passages and generates answers grounded in those passages.

**Grounding reduces hallucinations but cannot guarantee perfect accuracy.** When the available document content does not support an answer, DocuMind should clearly say it could not find the answer in the provided material.

## Goals
- Google sign-in and sign-out.
- Upload and manage each user's own documents.
- Extract and split document text into chunks.
- Generate embeddings and store chunks/vectors for semantic search.
- Ask questions about uploaded documents and display source references when available.
- Revisit previous chats and documents.
- Match the five approved UI reference images.

## Core User Flow
1. Visitor opens the login page and signs in with Google.
2. User uploads a supported document.
3. Backend stores the original file and processes text into chunks and embeddings.
4. User asks a question in a chat.
5. Backend retrieves relevant chunks from documents the user is allowed to access.
6. The LLM answers using the retrieved context.
7. The app shows the answer and source references, or a clear no-evidence response.

## Main Features
### Authentication
- Google sign-in and sign-out.
- User-specific access to documents and chats.

### Documents
- Upload supported files.
- Show document metadata and processing status.
- Store originals separately from extracted text and embeddings.
- View document content and available page/source information.

### Chat and Retrieval
- Create and revisit chats.
- Ask questions about selected documents.
- Semantic similarity search.
- Show source references where available.
- Do not invent answers when evidence is insufficient.

### Settings
- Profile/account and settings screen based on the design reference.
- Implement only settings actions whose behavior is defined.

## Scope
**In scope:** React + Vite, FastAPI, LangChain, Supabase Auth/PostgreSQL/Storage, pgvector, Google OAuth, document upload, semantic retrieval, grounded Q&A, chat history, and five UI pages.

**Not currently in scope:** general web search, model training, public document sharing, team collaboration, billing, OCR for scanned PDFs, and unsupported formats unless explicitly approved.

## Success Criteria
- Users can sign in and out.
- Users can upload a supported document and see processing status.
- Chunks and embeddings are searchable.
- Answers are grounded in retrieved document content.
- Insufficient evidence produces a clear no-answer response.
- Users cannot access other users' documents, chunks, or chats.
- The five screens are responsive and follow the approved references.

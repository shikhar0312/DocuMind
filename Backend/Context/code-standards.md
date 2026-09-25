# DocuMind — Code Standards

## General
- Make small, focused changes that implement one defined unit.
- Preserve working behavior unless the task requires a change.
- Use clear domain names: documents, chunks, chats, messages, sources.
- Validate external input at system boundaries.
- Never commit secrets, tokens, or real user documents.
- Avoid unnecessary dependencies and speculative abstractions.

## React and TypeScript
- Use TypeScript for frontend application code.
- Avoid `any`; use explicit types and narrow unknown values.
- Keep components focused and reusable when reuse is meaningful.
- Put API calls in a dedicated API/service layer.
- Handle loading, empty, success, and error states.
- Support keyboard access, visible focus, and responsive layouts.
- Never put privileged Supabase credentials in frontend environment variables.

## FastAPI and Python
- Use `uv` for dependency management and commands.
- Add packages with `uv add <package>` and run commands with `uv run <command>`.
- Organize routes, schemas, business logic, and persistence code as the backend grows.
- Use Pydantic models for request/response validation.
- Validate required configuration at startup.
- Return clear HTTP errors without exposing internal stack traces or secrets.

## API
- Use a consistent `/api/...` prefix for application endpoints.
- Define request and response schemas explicitly.
- Require authentication for user-owned documents, chats, and messages.
- Check ownership before reading, updating, or deleting resources.
- Return purpose-built response models where appropriate.

## Data
- Store original files in Supabase Storage.
- Store metadata, chunks, and embeddings in Supabase PostgreSQL with pgvector, once schema is finalized.
- Preserve source metadata such as page number where available.
- Scope queries to the authenticated user and enforce database policies.
- Keep secrets out of database records unless a separately approved design requires them.

## File Organization
- Frontend source: `Frontend/src/`
- Backend source: `Backend/app/`
- Context: `Backend/Context/`
- Design references: `Backend/Design/`
- Backend dependencies: `Backend/pyproject.toml` and `Backend/uv.lock`
- Keep `.env` out of version control; add a sanitized `.env.example` once configuration is defined.

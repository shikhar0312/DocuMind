# DocuMind — AI Workflow Rules

## Before Implementing
Read these files:
1. `Backend/Context/project-overview.md`
2. `Backend/Context/architecture.md`
3. `Backend/Context/ui-context.md`
4. `Backend/Context/code-standards.md`
5. `Backend/Context/ai-workflow-rules.md`
6. `Backend/Context/progress-tracker.md`

Inspect the relevant existing code and the matching images in `Backend/Design/` before editing.

## Planning
- Implement one clearly scoped feature at a time.
- Each unit should produce a visible or objectively verifiable result.
- Respect dependencies; build foundations before dependent features.
- Install only packages needed for the current unit.
- Do not invent product behavior, schema details, providers, or security decisions.
- Ask for clarification when a missing decision materially affects product behavior, architecture, security, or ownership.

## Implementation
- Follow the architecture, UI context, and code standards.
- Preserve working functionality.
- Keep changes limited to the requested scope.
- Never expose secrets or weaken authentication/ownership checks.
- Do not claim a placeholder is functional.
- RAG answers must be grounded in retrieved document evidence and clearly say when evidence is insufficient.

## Verification
Before marking a unit complete:
- Run relevant frontend type-check/build and backend checks.
- Verify behavior manually or with tests.
- Check loading, empty, and error states where relevant.
- Check responsive behavior for UI work.
- Confirm auth and ownership protections for protected features.
- Report checks not run; do not claim unverified success.

## Progress and Context
- Update `progress-tracker.md` after meaningful implementation changes.
- Use `[x]` only for completed and verified/confirmed work; use `[ ]` for incomplete work.
- Update context files when architecture, data, storage, auth, scope, UI conventions, or standards change.
- Keep unresolved decisions in the Open Questions section.

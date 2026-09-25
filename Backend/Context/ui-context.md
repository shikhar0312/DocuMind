# DocuMind — UI Context

## Theme
A clean, ChatGPT-inspired document workspace with a purple and soft-white identity. Prioritize clarity, readability, and a focused document-chat experience.

## Visual Direction
- Purple for primary actions, active navigation, and selected states.
- White or very light lavender backgrounds.
- White surfaces with subtle lavender-tinted borders.
- Dark charcoal/navy primary text and muted gray secondary text.
- Accessible status colors for processing, success, and errors.
- Use consistent design tokens; exact color values should be selected from the approved reference images.
- Modern sans-serif typography and consistent text hierarchy.
- Consistent rounded corners for cards, buttons, inputs, and composer.
- Use one consistent icon family.

## Page 1 — Login
- First screen for unauthenticated visitors.
- DocuMind branding and concise product explanation.
- Prominent “Continue with Google” action.
- Spacious purple/soft-white visual treatment.

## Page 2 — Chat Workspace
- Persistent left sidebar and central conversation area, inspired by ChatGPT.
- Sidebar: new chat, search, documents, recent chats, and account area near the bottom.
- Main area: current chat, messages, source references, and composer.
- Sidebar adapts/collapses on smaller screens.

## Page 3 — Document Upload
- Dedicated upload page or modal.
- Drag-and-drop area and browse action.
- File details and processing status.
- Clear uploading, processing, ready, and failure states.

## Page 4 — Document Viewer
- Readable document canvas with page navigation.
- Assistant panel beside the document on wide screens.
- Tabs/sections such as chat, summary, notes, and citations only where represented in the reference.
- Responsive layout that preserves document readability.

## Page 5 — Settings
- Profile/account, document management, preferences, security, and help sections as shown in the reference.
- Do not make visual placeholders appear functional if their behavior is not implemented.

## Reusable Components
Prefer reusable buttons, inputs, dialogs, badges, navigation items, document rows, chat messages, and source citations. Component library is not selected yet; inspect existing dependencies before adding one.

## Reference Images
Place the five approved images in `Backend/Design/` and use them as the visual source of truth:
1. Login
2. Chat workspace
3. Document upload
4. Document viewer
5. Settings

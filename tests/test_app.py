"""Tests for Streamlit application UI."""

from pathlib import Path
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parent.parent / "app.py"


def test_app_initialization_and_render():
    at = AppTest.from_file(str(APP_PATH))
    at.run(timeout=10)

    # Verify no unhandled exceptions occurred
    assert not at.exception

    # Check title
    titles = [t.value for t in at.title]
    assert "DocuMind" in titles

    # Check sidebar presence
    sidebar_headers = [h.value for h in at.sidebar.header]
    assert any("Knowledge Base" in h for h in sidebar_headers)

    # Check sidebar tabs
    tabs = [t.label for t in at.sidebar.tabs]
    assert "📁 Upload Files" in tabs
    assert "📝 Paste Text" in tabs


def test_app_chat_history_rendering():
    at = AppTest.from_file(str(APP_PATH))
    at.run(timeout=10)

    # Populate session messages manually
    at.session_state.messages = [
        {"role": "user", "content": "What is DocuMind?"},
        {
            "role": "assistant",
            "content": "DocuMind is a RAG document assistant.",
            "sources": [{"source": "overview.pdf", "page": 1, "file_type": "pdf"}],
            "has_sufficient_context": True,
        },
    ]
    at.run(timeout=10)

    assert not at.exception
    # Check that chat messages are rendered
    chat_messages = at.chat_message
    assert len(chat_messages) >= 2
    assert "What is DocuMind?" in chat_messages[0].markdown[0].value
    assert "DocuMind is a RAG document assistant." in chat_messages[1].markdown[0].value


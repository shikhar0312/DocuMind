"""DocuMind — RAG Document Assistant Streamlit Application.

Interactive user interface for document ingestion (PDF, DOCX, TXT, manual text),
collection management, persistent vector storage, and context-grounded Q&A chat.
"""

import sys
from pathlib import Path
import streamlit as st

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.document_loader import load_document, load_manual_text
from src.rag_chain import ask_rag
from src.text_splitter import split_documents
from src.vector_store import (
    add_documents_to_store,
    clear_vector_store,
    get_collection_stats,
    get_vector_store,
)

# Page configuration
st.set_page_config(
    page_title="DocuMind — RAG Document Assistant",
    page_icon=str(PROJECT_ROOT / "assets" / "documind_favicon.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)




# Premium DocuMind visual system
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root { --accent:#8B7CFF; --accent2:#6D5DFB; --ink:#F3F2FF; --muted:#A4A2B8; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    .stApp { background: radial-gradient(ellipse at 75% 0%, #1b1a35 0%, #101018 42%, #0c0c12 100%); }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { background:rgba(20,20,31,.96); border-right:1px solid #29283b; }
    [data-testid="stSidebar"] > div { padding-top:1.5rem; }
    .sidebar-brand { display:flex; align-items:center; gap:12px; margin:0 0 30px 2px; }
    .brand-mark { width:42px;height:42px;border-radius:14px;background:linear-gradient(135deg,#9D91FF,#6554E8);display:grid;place-items:center;color:white;font:800 22px Manrope;box-shadow:0 8px 24px #7565ff33; }
    .brand-name { color:#F7F6FF;font:700 17px Manrope;letter-spacing:-.4px; }
    .brand-subtitle { color:#8F8DA7;font-size:11px;margin-top:2px; }
    .sidebar-label,.eyebrow { color:#9B91FF;font-size:10px;font-weight:700;letter-spacing:1.8px;margin-bottom:12px; }
    .hero { padding:34px 0 25px; }
    .hero h1 { font:800 clamp(32px,4vw,48px)/1.12 Manrope,sans-serif; letter-spacing:-1.8px; color:#F6F5FF; margin:0 0 16px; }
    .hero h1 span { color:#9B91FF; }
    .hero p { color:#A6A4BA;font-size:15px;max-width:650px;line-height:1.7; }
    .welcome-card { display:flex;gap:16px;align-items:flex-start;padding:22px 24px;border:1px solid #34314F;border-radius:18px;background:linear-gradient(135deg,#1d1b35,#171722);color:#EDEBFF;margin:12px 0 24px; }
    .welcome-icon { display:grid;place-items:center;min-width:36px;height:36px;border-radius:12px;background:#7162F333;color:#A99FFF;font-size:20px; }
    .welcome-card strong { font:700 15px Manrope; }
    .welcome-card p { color:#A6A4BA;margin:6px 0 0;font-size:13px;line-height:1.6; }
    [data-testid="stChatInput"] { border:1px solid #39374F!important;border-radius:16px!important;background:#191923!important; }
    [data-testid="stChatInput"] textarea { color:#F4F2FF!important; }
    [data-testid="stChatMessage"] { border:1px solid #2D2B40;border-radius:16px;padding:16px 20px;background:#171720; }
    .stButton>button[kind="primary"] { background:linear-gradient(135deg,#8B7CFF,#6756E8);border:0;border-radius:11px;color:white;font-weight:700;min-height:44px;box-shadow:0 8px 20px #7565ff20; }
    .stButton>button[kind="primary"]:hover { border:0;background:linear-gradient(135deg,#A198FF,#7768F5); }
    .stButton>button { border-radius:10px;border-color:#39374F; }
    [data-testid="stFileUploader"] { border:1px dashed #48445F;border-radius:13px;background:#191923;padding:10px; }
    [data-testid="stMetric"] { background:#1B1A28;border:1px solid #302E43;border-radius:14px;padding:14px; }
    [data-testid="stMetricLabel"] { color:#A6A4BA; }
    [data-testid="stMetricValue"] { color:#F3F1FF; }
    .stTabs [data-baseweb="tab"] { color:#A6A4BA; }
    .stTabs [aria-selected="true"] { color:#A99FFF!important; }
    hr { border-color:#302E43!important; }
    h2,h3 { font-family:Manrope,sans-serif!important;color:#F1F0FF!important; }
    </style>
    """,
    unsafe_allow_html=True,
)

def initialize_session_state() -> None:
    """Initialize chat message history and UI session variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []


def render_sidebar(vector_store) -> None:
    """Render sidebar controls for ingestion, collection stats, and management."""
    with st.sidebar:
        

        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="brand-mark">D</div>
                <div>
                    <div class="brand-name">DocuMind</div>
                    <div class="brand-subtitle">Your knowledge workspace</div>
                </div>
            </div>
            <div class="sidebar-label">KNOWLEDGE BASE</div>
            """,
            unsafe_allow_html=True,
        )

        # Tabbed interface for document upload vs raw text input
        upload_tab, text_tab = st.tabs(["＋ Upload files", "✎ Add text"])

        with upload_tab:
            uploaded_files = st.file_uploader(
                "Add documents",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                help="Upload one or multiple documents to index into your knowledge base.",
            )

            if st.button("Add to knowledge base", type="primary", use_container_width=True):
                if not uploaded_files:
                    st.warning("Please select at least one file to upload.")
                else:
                    process_uploaded_files(uploaded_files, vector_store)

        with text_tab:
            manual_title = st.text_input(
                "Source Title (optional)",
                value="",
                placeholder="e.g. Project Notes or Meeting Summary",
            )
            manual_content = st.text_area(
                "Text Content",
                height=180,
                placeholder="Paste notes, articles, or text here...",
            )

            if st.button("Add text to knowledge base", type="primary", use_container_width=True):
                if not manual_content.strip():
                    st.warning("Please enter some text to ingest.")
                else:
                    process_manual_text(manual_title, manual_content, vector_store)

        st.divider()

        # Display collection statistics
        render_collection_stats(vector_store)

        st.divider()

        # Clear Collection Button
        if st.button("Clear knowledge base", type="secondary", use_container_width=True):
            clear_knowledge_base(vector_store)


def process_uploaded_files(uploaded_files, vector_store) -> None:
    """Load, split, and index uploaded files into the vector database."""
    total_new_chunks = 0
    success_files = []
    error_files = []

    progress_bar = st.progress(0, text="Starting document ingestion...")
    total_files = len(uploaded_files)

    for idx, uploaded_file in enumerate(uploaded_files, start=1):
        filename = uploaded_file.name
        progress_bar.progress(
            idx / total_files, text=f"Processing ({idx}/{total_files}): {filename}"
        )
        try:
            # Load raw document into LangChain Documents
            docs = load_document(uploaded_file, filename=filename)
            # Split documents into overlapping chunks
            chunks = split_documents(docs)
            if chunks:
                add_documents_to_store(chunks, vector_store=vector_store)
                total_new_chunks += len(chunks)
                success_files.append(filename)
            else:
                error_files.append((filename, "Document yielded no text chunks."))
        except Exception as e:
            error_files.append((filename, str(e)))

    progress_bar.empty()

    if success_files:
        st.success(
            f"Successfully indexed {len(success_files)} document(s) "
            f"({total_new_chunks} chunks added)."
        )
    for fname, err in error_files:
        st.error(f"Error processing '{fname}': {err}")

    st.rerun()


def process_manual_text(title: str, text: str, vector_store) -> None:
    """Load, split, and index manually entered text into the vector database."""
    source_name = title.strip() or "manual_text"
    try:
        docs = load_manual_text(text, source_name=source_name)
        chunks = split_documents(docs)
        if chunks:
            add_documents_to_store(chunks, vector_store=vector_store)
            st.success(f"Indexed '{source_name}' ({len(chunks)} chunks added).")
            st.rerun()
        else:
            st.warning("No content could be extracted from the text.")
    except Exception as e:
        st.error(f"Failed to ingest text: {e}")


def render_collection_stats(vector_store) -> None:
    """Display real-time statistics on indexed documents and chunks."""
    st.subheader("Collection Stats")
    try:
        stats = get_collection_stats(vector_store)
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Chunks", stats["total_chunks"])
        with col2:
            st.metric("Documents", stats["source_count"])

        if stats["unique_sources"]:
            with st.expander("Indexed Files", expanded=False):
                for src in stats["unique_sources"]:
                    st.write(f"- `{src}`")
        else:
            st.caption("No documents currently indexed.")
    except Exception as e:
        st.warning(f"Could not load stats: {e}")


def clear_knowledge_base(vector_store) -> None:
    """Clear all vector collection records and reset chat history."""
    try:
        clear_vector_store(vector_store)
        st.session_state.messages = []
        st.success("Knowledge base and chat history cleared successfully.")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to clear knowledge base: {e}")


def render_chat_interface(vector_store) -> None:
    """Render main chat interface with conversation history and grounded responses."""
    st.title("DocuMind")
    st.caption(
        "Ask questions grounded strictly in your uploaded knowledge base. "
        "Every answer cites source documents and page numbers."
    )

    # Empty state guidance
    stats = get_collection_stats(vector_store)
    if stats["total_chunks"] == 0 and not st.session_state.messages:
        st.markdown(
            """
            <div class="welcome-card">
                <div class="welcome-icon">✦</div>
                <div>
                    <strong>Your workspace is ready</strong>
                    <p>Upload PDFs, Word documents, or text—or add notes manually. Then ask a question to explore your content.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Render message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Display source citations if present
            sources = message.get("sources")
            if sources:
                with st.expander(f"📑 Sources & Citations ({len(sources)})", expanded=False):
                    for src in sources:
                        page_str = f" • Page {src['page']}" if src.get("page") is not None else ""
                        file_type_str = f"[{src.get('file_type', 'doc').upper()}]"
                        st.markdown(
                            f"- **{src.get('source', 'Unknown')}** {page_str} `{file_type_str}`"
                        )

    # Chat input box
    if user_prompt := st.chat_input("Ask a question about your documents..."):
        # Display user message immediately
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("Searching documents & generating grounded response..."):
                try:
                    response = ask_rag(user_prompt, vector_store=vector_store)
                    st.markdown(response.answer)

                    if response.sources:
                        with st.expander(
                            f"📑 Sources & Citations ({len(response.sources)})", expanded=False
                        ):
                            for src in response.sources:
                                page_str = (
                                    f" • Page {src['page']}"
                                    if src.get("page") is not None
                                    else ""
                                )
                                file_type_str = f"[{src.get('file_type', 'doc').upper()}]"
                                st.markdown(
                                    f"- **{src.get('source', 'Unknown')}** {page_str} `{file_type_str}`"
                                )

                    # Save to session history
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response.answer,
                            "sources": response.sources,
                            "has_sufficient_context": response.has_sufficient_context,
                        }
                    )
                except Exception as e:
                    error_msg = f"An error occurred while generating the answer: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": error_msg,
                            "sources": [],
                            "has_sufficient_context": False,
                        }
                    )


def main() -> None:
    """Main application entrypoint."""
    initialize_session_state()
    try:
        vector_store = get_vector_store()
    except Exception as e:
        st.error(f"Failed to connect to vector database: {e}")
        return

    render_sidebar(vector_store)
    render_chat_interface(vector_store)


if __name__ == "__main__":
    main()

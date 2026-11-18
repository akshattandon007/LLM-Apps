"""
app.py — JunkJudge Streamlit UI.

Upload your municipal recycling/waste-disposal PDFs (or paste text),
then ask plain-English questions about what goes where.
"""

import os
import tempfile
from pathlib import Path

import streamlit as st

from document_loader import load_and_chunk, load_and_chunk_from_text
from rag_engine import RAGEngine


# ── Page config ─────────────────────────────────────────────────────

st.set_page_config(
    page_title="JunkJudge",
    page_icon="♻️",
    layout="centered",
)

st.title("♻️ JunkJudge")
st.markdown(
    "Upload your **municipal recycling & waste guidelines** (PDF or paste text), "
    "then ask what goes where. No more guessing at the bin."
)

# ── Session state ───────────────────────────────────────────────────

if "engine" not in st.session_state:
    st.session_state.engine = None
if "docs_loaded" not in st.session_state:
    st.session_state.docs_loaded = False

# ── Sidebar: document loading ───────────────────────────────────────

with st.sidebar:
    st.header("📄 Load Your Guidelines")

    upload_method = st.radio("Source", ["Upload PDF(s)", "Paste text"], index=0)

    pdf_files = None
    pasted_text = None

    if upload_method == "Upload PDF(s)":
        pdf_files = st.file_uploader(
            "Choose PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload your city/county recycling rules PDF.",
        )
    else:
        source_name = st.text_input("Label (e.g., 'Austin Recycling Guide')", "My Guidelines")
        pasted_text = st.text_area(
            "Paste the text of your recycling rules",
            height=200,
            placeholder="Paste the content from your municipality's website or PDF here...",
        )

    if st.button("📥 Load Documents", type="primary"):
        chunks = []

        if upload_method == "Upload PDF(s)" and pdf_files:
            with st.spinner(f"Processing {len(pdf_files)} PDF(s)..."):
                temp_paths = []
                for f in pdf_files:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    tmp.write(f.getbuffer())
                    tmp.close()
                    temp_paths.append(tmp.name)

                try:
                    chunks = load_and_chunk(temp_paths)
                finally:
                    for p in temp_paths:
                        try:
                            os.unlink(p)
                        except OSError:
                            pass

        elif upload_method == "Paste text" and pasted_text:
            with st.spinner("Processing pasted text..."):
                chunks = load_and_chunk_from_text({source_name: pasted_text})

        else:
            st.warning("Please provide documents first.")
            st.stop()

        if not chunks:
            st.error("No text could be extracted. Check the file(s).")
            st.stop()

        try:
            engine = RAGEngine(chunks)
            st.session_state.engine = engine
            st.session_state.docs_loaded = True
            st.success(f"Loaded {len(chunks)} document chunks. Ready to answer questions!")
        except Exception as e:
            st.error(f"Failed to build search index: {e}")

    if st.session_state.docs_loaded:
        st.info(f"✅ {st.session_state.engine.chunks.__len__() if hasattr(st.session_state.engine, 'chunks') else ''} chunks indexed")

# ── Main: Q&A ───────────────────────────────────────────────────────

if not st.session_state.docs_loaded:
    st.info(
        "👈 **Get started:** Load your municipality's recycling/waste guidelines "
        "using the sidebar, then come back here to ask questions."
    )
    st.markdown("---")
    st.markdown("### Example questions you can ask")
    st.markdown(
        """
- *"Can I recycle pizza boxes?"*
- *"What day is bulk pickup?"*
- *"Is #5 plastic recyclable here?"*
- *"How do I dispose of old paint?"*
- *"Can I put glass in the curbside bin?"*
        """
    )
    st.stop()

# ── Q&A interface ───────────────────────────────────────────────────

st.header("💬 Ask About Your Rules")

question = st.text_input(
    "What do you want to know?",
    placeholder="e.g., Can I recycle pizza boxes?",
    key="question_input",
)

col1, col2 = st.columns([1, 5])
with col1:
    ask_btn = st.button("🔍 Ask", type="primary")
with col2:
    clear_btn = st.button("🗑️ Clear history")

if clear_btn:
    st.session_state.pop("chat_history", None)
    st.rerun()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if ask_btn and question:
    with st.spinner("Searching your guidelines..."):
        result = st.session_state.engine.query(question)

    st.session_state.chat_history.append({"question": question, "result": result})

# Display chat history
for entry in st.session_state.chat_history:
    with st.chat_message("user"):
        st.markdown(entry["question"])

    with st.chat_message("assistant"):
        st.markdown(entry["result"]["answer"])

        if entry["result"]["sources"]:
            with st.expander("📎 Sources"):
                for i, src in enumerate(entry["result"]["sources"], 1):
                    st.markdown(
                        f"**{i}.** From `{src['source']}` (page {src['page']})\n\n"
                        f"> {src['text'][:300]}{'...' if len(src['text']) > 300 else ''}"
                    )

# Also allow follow-up via chat input
follow_up = st.chat_input("Ask a follow-up question...")
if follow_up:
    with st.spinner("Searching your guidelines..."):
        result = st.session_state.engine.query(follow_up)

    st.session_state.chat_history.append({"question": follow_up, "result": result})
    st.rerun()
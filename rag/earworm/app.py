"""Earworm — Streamlit web app for podcast transcript search."""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from models import get_db, init_db, list_shows, list_episodes, get_episode
from embedder import load_model, load_index, load_id_map
from searcher import search_chunks, synthesize_answer, format_excerpt


st.set_page_config(
    page_title="Earworm — Podcast Search",
    page_icon="🎙️",
    layout="wide",
)

# --- Stateful init ---
@st.cache_resource
def init_resources():
    conn = get_db()
    init_db(conn)
    model = load_model()
    index = load_index()
    id_map = load_id_map()
    return conn, model, index, id_map


conn, model, index, id_map = init_resources()

# --- Sidebar ---
st.sidebar.title("🎙️ Earworm")
st.sidebar.caption("Remember that episode? I will find it for you.")

# Show filters
shows = list_shows(conn)
show_names = ["All shows"] + [s["name"] for s in shows]
selected_show = st.sidebar.selectbox("Filter by show", show_names)

date_range = st.sidebar.selectbox(
    "Date range", ["Any time", "Past week", "Past month", "Past year"]
)

top_k = st.sidebar.slider("Results", 3, 20, 8)

use_llm = st.sidebar.checkbox(
    "Synthesize with LLM", value=False,
    help="Use AI to synthesize a coherent answer from results (requires OPENROUTER_API_KEY)"
)

# Stats
from models import stats as db_stats
s = db_stats(conn)
st.sidebar.metric("Shows", s["shows"])
st.sidebar.metric("Episodes", s["episodes"])
st.sidebar.metric("Chunks", s["chunks"])
if index:
    st.sidebar.metric("Indexed", index.ntotal)
else:
    st.sidebar.caption("No index yet — ingest some transcripts first.")


# --- Main ---
st.title("Earworm")
st.caption("Semantic search across your podcast library.")

query = st.text_input(
    "Search",
    placeholder="e.g. what did they say about the Fermi paradox?",
    key="search_query",
)

if query:
    with st.spinner("Searching..."):
        # Compute date filter
        date_from = None
        if date_range != "Any time":
            from datetime import datetime, timedelta
            days = {"Past week": 7, "Past month": 30, "Past year": 365}
            date_from = (datetime.now() - timedelta(days=days[date_range])).strftime("%Y-%m-%d")

        # Search
        results = search_chunks(query, model, index, id_map, top_k=top_k * 2)

        # Apply show filter
        if selected_show != "All shows":
            results = [(r, s) for r, s in results if r["show_name"] == selected_show]

        # Apply date filter
        if date_from:
            results = [(r, s) for r, s in results if (r["pub_date"] or "") >= date_from]

        # Trim to top_k
        results = results[:top_k]

    if not results:
        st.warning("No results found. Try a different query or ingest some transcripts first.")
    else:
        # LLM Synthesis
        if use_llm:
            with st.spinner("Synthesizing answer..."):
                answer = synthesize_answer(query, results)
            if answer:
                st.markdown("### AI Answer")
                st.markdown(answer)
                st.divider()

        # Results
        st.markdown(f"### Top {len(results)} results")

        for i, (chunk, score) in enumerate(results):
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{chunk['show_name']}** — *{chunk['episode_title']}*")
                with col2:
                    st.caption(f"Match: {score:.2f}")

                st.caption(
                    f"📅 {chunk['pub_date'] or 'unknown date'}  |  "
                    f"📍 position ~char {chunk['start_char'] or 0}"
                )

                # Show context snippet
                st.markdown(
                    f'<div style="background:#1e1e1e;padding:12px;border-radius:8px;'
                    f'border-left:3px solid #ff4b4b;margin:8px 0;">'
                    f'{chunk["text"]}</div>',
                    unsafe_allow_html=True,
                )

                # Link to full transcript or audio
                if chunk.get("audio_url"):
                    st.caption(f"🔗 [Original episode]({chunk['audio_url']})")

                # Expand full transcript
                with st.expander("View full transcript"):
                    episode = get_episode(conn, chunk["episode_id"])
                    if episode and episode["transcript"]:
                        st.text_area(
                            "Transcript",
                            episode["transcript"],
                            height=200,
                            key=f"tx_{chunk['id']}",
                            disabled=True,
                        )

                if i < len(results) - 1:
                    st.divider()

elif not query:
    # Empty state
    show_count = s["shows"]
    if show_count == 0:
        st.info(
            "No transcripts indexed yet. Use the CLI to ingest some:\n\n"
            "```bash\n"
            "python ingest.py rss <feed_url> <show_name>\n"
            "python ingest.py file <path> <show_name> <episode_title>\n"
            "python ingest.py audio <path> <show_name> <episode_title>\n"
            "```"
        )
    else:
        st.success(
            f"Ready to search across {s['episodes']} episodes from {show_count} shows. "
            "Type a query above."
        )

# --- Browse library ---
with st.expander("Browse library"):
    tab1, tab2 = st.tabs(["Episodes", "Shows"])
    with tab1:
        eps = list_episodes(conn)
        if eps:
            for ep in eps:
                st.markdown(f"**{ep['show_name']}** — *{ep['title']}*")
                st.caption(f"{ep['pub_date'] or '?'}")
        else:
            st.caption("No episodes yet.")
    with tab2:
        if shows:
            for show in shows:
                st.markdown(f"**{show['name']}**")
                if show.get("feed_url"):
                    st.caption(show["feed_url"])
        else:
            st.caption("No shows yet.")
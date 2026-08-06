# Earworm

🎙️ **Remember that episode? I will find it for you.**

Earworm is a RAG-powered podcast transcript search engine. It ingests podcast
transcripts, chunks them at semantic boundaries, embeds them with
sentence-transformers, and lets you search across ALL your shows with natural
language queries.

## Features

- **RSS ingestion** — point at a podcast RSS feed, Earworm pulls episode
  metadata and transcripts automatically.
- **Manual transcript uploads** — drag in plain text, SRT, or VTT files.
- **Optional audio transcription** — feed it .mp3 files and it runs Whisper
  to transcribe.
- **Semantic chunking** — splits at topic boundaries (sentence embedding
  similarity), not arbitrary character counts.
- **FAISS vector search** — fast similarity search across all chunks.
- **LLM answer synthesis** — optionally uses OpenRouter to synthesize a
  coherent answer with citations.

## Quick Start

```bash
# 1. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ingest some transcripts
python ingest.py rss https://feeds.example.com/podcast.xml "My Podcast"
python ingest.py file /path/to/transcript.txt "My Podcast" "Episode 42"
python ingest.py audio /path/to/episode.mp3 "My Podcast" "Episode 42"

# 4. Launch the search UI
streamlit run app.py
```

## CLI Reference

```
python ingest.py rss <feed_url> <show_name>
    Ingest all episodes from an RSS feed.

python ingest.py file <path> <show_name> <episode_title> [--date YYYY-MM-DD]
    Ingest a transcript file (txt, srt, vtt).

python ingest.py audio <path> <show_name> <episode_title> [--date YYYY-MM-DD]
    Transcribe an audio file with Whisper and ingest.

python ingest.py stats
    Show database and index statistics.

python ingest.py rebuild-index
    Rebuild the FAISS index from the database.
```

## LLM Synthesis (optional)

Set the `OPENROUTER_API_KEY` environment variable to enable AI-powered answer
synthesis in the search UI:

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
```

Then toggle "Synthesize with LLM" in the sidebar.

## Architecture

```
app.py          — Streamlit web UI
ingest.py       — CLI: RSS, file, and audio ingestion
chunker.py      — Semantic chunking (sentence embedding similarity)
embedder.py     — FAISS index management
searcher.py     — Search + LLM answer synthesis
models.py       — SQLite schema and queries
data/           — Database + FAISS index (auto-created)
```

## Tech Stack

- **Python 3.11+**
- **sentence-transformers** (all-MiniLM-L6-v2) — embeddings
- **FAISS** — vector similarity search
- **SQLite** — transcript and metadata storage
- **Streamlit** — web UI
- **feedparser** — RSS ingestion
- **openai-whisper** (optional) — audio transcription
- **OpenRouter API** (optional) — LLM answer synthesis
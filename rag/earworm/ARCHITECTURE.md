# Earworm — Architecture

## 1. System Overview

Earworm is a RAG-powered semantic search engine for podcast transcripts. It ingests transcripts from RSS feeds, manual uploads (txt/srt/vtt), or optional Whisper transcription, chunks them at topical boundaries using sentence-embedding similarity, indexes the chunks with FAISS, and provides a Streamlit web UI for cross-show semantic search with optional LLM-powered answer synthesis.

```
User Query -> Embed -> FAISS Search -> [Optional: LLM Synthesis] -> Ranked Results + Citations
```

## 2. Data Flow

```
RSS Feed ─► feedparser ─► Episode Metadata ─► SQLite
                          Transcript (HTML-stripped description)

File Upload ─► parse_srt/parse_vtt ─► Plain Text ─► SQLite

Audio File ─► Whisper ─► Plain Text ─► SQLite

SQLite Transcript ─► Semantic Chunker ─► Chunks ─► SentenceTransformer Embedding ─► FAISS Index
                                                      └─► SQLite (chunks table)
```

## 3. Ingestion Pipeline

Three entry points via `ingest.py`:

- **RSS** (`ingest.py rss <url> <show>`): Uses `feedparser` to parse feeds, extracts episode titles, descriptions, publication dates, and audio URLs. HTML-stripped descriptions serve as transcripts when available.

- **File** (`ingest.py file <path> <show> <title>`): Loads plain text, SRT, or VTT files. SRT/VTT parsers strip timestamps and formatting to extract clean transcript text.

- **Audio** (`ingest.py audio <path> <show> <title>`): Runs `openai-whisper` for transcription (optional dependency).

Each ingestion path:
1. Inserts/upserts the show in `shows` table
2. Inserts/upserts the episode in `episodes` table
3. Clears old chunks for that episode
4. Runs `chunk_transcript()` to generate semantic chunks
5. Embeds chunks with `SentenceTransformer`
6. Stores chunks in the `chunks` table
7. Appends embeddings to the FAISS index incrementally

## 4. Semantic Chunking

`chunker.py` implements boundary detection via sentence embedding similarity:

1. Split transcript into sentences (`_split_sentences`)
2. Compute sentence embeddings (`all-MiniLM-L6-v2`, 384-dim)
3. Walk through sentences sequentially. Compare cosine similarity between adjacent sentence embeddings.
4. Insert a chunk boundary when:
   - **Semantic break**: similarity drops below threshold (default 0.35) AND current chunk exceeds `min_chars` (400)
   - **Force break**: adding this sentence would exceed `max_chars` (1100) AND current chunk meets `min_chars`
5. Merge trailing small chunks (< min_chars) into the previous chunk

This ensures chunks represent coherent topical segments (~500-1000 chars), not arbitrary character slices.

## 5. FAISS Index Design

- **Index type**: `IndexFlatIP` (inner product) — equivalent to cosine similarity because embeddings are L2-normalized (`normalize_embeddings=True`)
- **Dimensionality**: 384 (matching all-MiniLM-L6-v2)
- **ID mapping**: Pickle-serialized `dict[int, int]` mapping FAISS internal positions to SQLite `chunks.id`
- **Incremental updates**: New chunks are appended to the index; `rebuild-index` rebuilds from scratch
- **Storage**: `data/index/faiss.index` and `data/index/id_map.pkl`

## 6. Search Flow

`searcher.py`:

1. User query → embed with same SentenceTransformer model
2. FAISS search returns top-K chunks by similarity score
3. Chunk IDs resolved to full rows via SQLite JOIN (chunks → episodes → shows)
4. Results ranked by FAISS score, filtered by show and date range in the UI
5. **Optional LLM synthesis**: Retrieved chunks formatted as excerpts with show/episode/date/position metadata → OpenRouter API → coherent answer with inline citations

## 7. Data Model (SQLite)

```
shows
├── id (PK)
├── name (UNIQUE)
├── feed_url
└── created_at

episodes
├── id (PK)
├── show_id (FK → shows.id)
├── title
├── description
├── pub_date
├── audio_url
├── source_file
├── transcript (full text)
├── ingested_at
└── UNIQUE(show_id, title)

chunks
├── id (PK)
├── episode_id (FK → episodes.id)
├── chunk_index
├── text
├── start_char
├── end_char
├── token_count
└── created_at
```

## 8. LLM Integration

`searcher.py` uses OpenRouter's chat completions API when `OPENROUTER_API_KEY` is set. The prompt template includes:
- Retrieved chunks formatted as `[Show | Episode | Date | Position]` blocks
- Rules: synthesize concisely, cite sources, don't hallucinate
- Model defaults to `openai/gpt-4o-mini`, configurable

## 9. Web UI (Streamlit)

`app.py`:
- **Sidebar**: Show filter, date range, result count slider, LLM synthesis toggle, library stats
- **Search**: Text input with semantic search
- **Results**: Show name + episode title, date, match score, transcript snippet (dark-themed card), "View full transcript" expander, link to original audio
- **Browse**: Episodes and shows tabs for library exploration
- **Empty state**: Shows CLI usage instructions when no data is indexed

## 10. Deployment

- **Dependencies**: `pip install -r requirements.txt`
- **Run**: `streamlit run app.py`
- **Ingest first**: `python ingest.py rss <feed_url> <show_name>`
- **LLM**: Set `OPENROUTER_API_KEY` for answer synthesis
- **Chroma/FAISS**: Uses FAISS CPU (`faiss-cpu`). For >100K chunks, consider switching to `faiss-gpu` or an IVF index

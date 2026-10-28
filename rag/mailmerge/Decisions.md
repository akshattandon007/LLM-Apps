# Decisions.md — MailMerge

## 1. CLI vs Web Interface
**Chosen**: CLI with subcommands (`argparse` + `__main__.py`)
**Rejected**: Flask/FastAPI web UI, Streamlit dashboard
**Why**: MailMerge processes local files. A web server adds setup overhead, port management, and browser dependency. CLI is simpler, scriptable, and works headless on VPS/desktop.

## 2. MBOX as Input Format
**Chosen**: Standard MBOX (mboxrd variant)
**Rejected**: IMAP/OAuth direct mailbox access, Maildir, MSG/EML per-file
**Why**: MBOX is the universal export format for Gmail (Takeout), Thunderbird, and Apple Mail. Direct IMAP would require OAuth credentials, scopes, and network — violating the "fully offline" constraint. MBOX gives us one file, no network, no auth.

## 3. ChromaDB for Vector Storage
**Chosen**: ChromaDB (PersistentClient, local filesystem)
**Rejected**: FAISS (no metadata filters), Qdrant (client-server, overkill), SQLite + custom ANN (reinvent wheel)
**Why**: ChromaDB is lightweight, persistent, supports metadata filters out of the box, and runs embedded without a server. FAISS would need a separate metadata store + serialization layer. ChromaDB's `where` clause lets us filter by sender/date without extra code.

## 4. sentence-transformers (all-MiniLM-L6-v2) for Embeddings
**Chosen**: `all-MiniLM-L6-v2` via sentence-transformers
**Rejected**: OpenAI embeddings (paid, API key, network), TF-IDF (no semantics), larger models like `all-mpnet-base-v2` (slower, bigger)
**Why**: `all-MiniLM-L6-v2` is 80MB, runs on CPU in ~50ms per query, and gives good semantic retrieval. No API key, no network. It's the best accuracy/speed trade-off for local use.

## 5. Character-Based Chunking with Paragraph Awareness
**Chosen**: Split by paragraph break (`\n\n`), fallback to sentence boundary
**Rejected**: Token-based chunking (tiktoken), fixed-size N-char sliding window
**Why**: Token-based needs a tokenizer loaded per-email. Paragraph-boundary preserves semantic units (a paragraph is usually one idea). Overlap ensures context continuity between chunks. Email bodies are usually short, so aggressive chunking isn't needed.

## 6. Single-Colleciton Model
**Chosen**: One ChromaDB collection per user, all email chunks together
**Rejected**: One collection per MBOX file, one collection per sender
**Why**: Cross-email search is the main use case. Multiple collections would force the user to query N collections and merge results. Metadata (sender, date) is stored per-chunk for filtering when needed.

## 7. L2 Distance → Similarity Score
**Chosen**: Convert ChromaDB's L2 distance to `1/(1+distance)` similarity
**Rejected**: Raw distance, cosine similarity with manual normalization
**Why**: ChromaDB returns L2 by default. The 1/(1+d) transform gives a 0-1 score that's intuitive for users (87% match feels right). Cosine would require normalizing during both store and query — more code, same result.

## 8. Chunk ID via Hash
**Chosen**: MD5 hash of `message_id:chunk_index:text_preview`
**Rejected**: UUID4, auto-increment, message_id alone
**Why**: Deterministic — re-ingesting the same file produces the same IDs, so upserts are idempotent. UUID4 changes on re-run, causing duplicates. Auto-increment doesn't survive DB rebuild.

## 9. Text Extraction from Multipart Emails
**Chosen**: Walk MIME parts, extract `text/plain` only, fallback latin-1
**Rejected**: Convert HTML→text, extract attachments, decode all charsets fully
**Why**: Most emails have a `text/plain` alternative. HTML→text conversion (beautifulsoup) adds a heavy dep for an edge case. Attachments aren't searchable text. Latin-1 fallback handles the common encoding issues.

## 10. Separate `ingest` and `search` Commands
**Chosen**: Two distinct subcommands (ingest once, search many times)
**Rejected**: Single auto-detect command, background daemon watching MBOX
**Why**: Ingest is a batch operation (slow, ~1-2 minutes for 10K emails). Search is interactive. Keeping them separate keeps the UX clear and avoids surprising latency.

## 11. Batch Embedding During Ingest
**Chosen**: Batch of 100 chunks per `encode()` call
**Rejected**: One chunk at a time, all chunks at once
**Why**: Mini-batching (100) utilizes sentence-transformers' internal batching efficiently without OOM on large archives. One-at-a-time is 100x slower. All-at-once can OOM on 50K+ archives.

## 12. Default DB Directory at `~/.mailmerge/chroma`
**Chosen**: `~/.mailmerge/chroma` as the default ChromaDB path
**Rejected**: CWD-based `.mailmerge/`, system-wide `/var/lib/mailmerge/`
**Why**: User home avoids permission issues and survives reinstalls. CWD would lose the index if you change directories. System dirs need sudo.

## 13. pytest for Testing
**Chosen**: pytest with unit tests for chunking, extraction, models
**Rejected**: unittest (verbose), no tests (risky)
**Why**: pytest is standard, concise, and gives readable failure output. Tests cover the parsing and chunking logic — the core that's most likely to break on real email data.

## 14. No Web Server or GUI
**Chosen**: Pure CLI tool
**Rejected**: Built-in HTTP interface for browser search
**Why**: The RAG category is about *retrieval*, not presentation. A web UI would double the codebase and is a future enhancement (can be added as a separate project consuming the same ChromaDB index).
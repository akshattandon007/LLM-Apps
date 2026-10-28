# MailMerge 📧🔍

**Offline RAG over your email archives** — import your Gmail/Outlook Takeout `.mbox` file and search it locally using natural language. No cloud, no API keys, no data leaves your machine.

## What It Does

- Parse MBOX email exports (Google Takeout, Thunderbird, Outlook)
- Chunk email bodies with paragraph-aware splitting
- Embed chunks using `all-MiniLM-L6-v2` (sentence-transformers)
- Store vectors in a local ChromaDB index
- Query with natural language — MailMerge finds the most relevant emails by *meaning*, not just keyword match

## Why

You've got 10,000+ emails in your inbox. Keyword search (Ctrl+F) fails when you don't remember exact phrasing. MailMerge finds "that hotel confirmation from my Italy trip" even when the email says "Booking.com — Your Reservation at Hotel Roma."

## Quick Start

### 1. Export your email

- **Gmail**: Google Takeout → select only Mail → download → the `.mbox` file is in `Takeout/Mail/All mail Including Spam and Trash.mbox`
- **Thunderbird**: right-click folder → Export as MBOX
- **Outlook**: use `MFCMAPI` or a third-party MBOX converter

### 2. Ingest

```bash
python3 -m mailmerge ingest ~/Takeout/Mail/All\ mail.mbox
```

This parses every email, extracts plain text, chunks it, embeds it, and stores vectors in `~/.mailmerge/chroma/`. First run downloads the embedding model (~80MB).

### 3. Search

```bash
python3 -m mailmerge search "hotel confirmation from my Italy trip"
```

Output:

```
============================================================
  Top 5 results for: "hotel confirmation from my Italy trip"
============================================================

  [1] 87% match
      From: bookings@hotelroma.it
      Subject: Booking.com — Your Reservation at Hotel Roma
      Date: Tue, 14 Mar 2024 10:30:00 +0100
      Snippet: Dear Guest, thank you for booking Hotel Roma. Your reservation for 2 adults, check-in 15...

  [2] 72% match
      From: noreply@expedia.com
      Subject: Expedia — Flight confirmation MXP-JFK
      Date: ...
```

### 4. Check status

```bash
python3 -m mailmerge status
# MailMerge index: 12543 chunks in ChromaDB at /home/user/.mailmerge/chroma
```

## Commands

| Command | Description |
|---------|-------------|
| `ingest <mbox>` | Parse and index an MBOX file |
| `search <query>` | Search the archive with natural language |
| `status` | Show index size and location |
| `--db-dir <path>` | Override default ChromaDB location |
| `--top-k <N>` | Number of search results (default 10) |
| `--chunk-size <N>` | Character chunk size (default 800) |

## How It Works (Pipeline)

```
📁 .mbox → parse (mailbox module) → extract plain text
  → paragraph-aware chunking → embed (all-MiniLM-L6-v2)
  → store in ChromaDB → query (same model) → ranked results
```

## Tests

```bash
cd /tmp/mailmerge && python3 -m pytest mailmerge/tests/ -v
```

## Privacy

Everything runs locally. No data is sent to any server. The embedding model (`all-MiniLM-L6-v2`) downloads once on first run and caches locally. The ChromaDB index stays on your machine at `~/.mailmerge/chroma/`.

## License

MIT
# Notion Agent

A Claude Opus 4.7–powered agent that does retrieval **properly** over a Notion
workspace. It crawls every page your integration can see, chunks them,
maintains a local vector index, and uses Claude's tool-use API to answer
cross-page questions with page citations — and to write back into your
workspace.

This fixes the top Reddit complaint about Notion's built-in Q&A (*"it doesn't
know your workspace, it just searches it"*) by layering real semantic
retrieval on top of the Notion API.

---

## Features

- **Semantic search** across your whole workspace using a local
  `sentence-transformers` + NumPy vector index — no cloud vector DB, no
  heavyweight FAISS dependency.
- **Cross-page synthesis**: Claude decomposes complex questions into multiple
  narrow searches, then stitches results together with page citations.
- **Read & write**: fetch a page's full content, or append new H2 sections to
  pages by ID or URL.
- **CLI-first**: one-shot `ask`, interactive `chat`, or direct `read` /
  `append` / `index` / `stats` subcommands.
- **Persistent local index** stored at `~/.notion_agent/index/` — embed once,
  query many times.

---

## Architecture

```
 ┌──────────────┐       ┌──────────────────┐       ┌────────────────────┐
 │   CLI        │──────▶│  NotionAgent     │──────▶│  Claude Opus 4.7   │
 │  (argparse)  │       │  (tool-use loop) │◀──────│  /v1/messages      │
 └──────────────┘       └─────────┬────────┘       └────────────────────┘
                                  │
                                  ▼
                        ┌───────────────────┐
                        │    ToolRunner     │
                        └─────┬───────┬─────┘
                              │       │
               ┌──────────────┘       └──────────────┐
               ▼                                     ▼
       ┌────────────────┐                  ┌──────────────────┐
       │ NotionClient   │                  │   VectorStore    │
       │  Wrapper       │                  │  (numpy + MiniLM)│
       │  (Notion API)  │                  └────────┬─────────┘
       └────────────────┘                           │
                                               reads/writes
                                                    ▼
                                           ~/.notion_agent/index/
```

---

## Setup

### 1. Create a Notion integration

1. Go to https://www.notion.so/profile/integrations → **New integration**.
2. Copy the **Internal Integration Token** (starts with `ntn_`).
3. In Notion, open each page or database you want the agent to see →
   click `···` → **Connections** → add your integration. Child pages inherit
   access from their parent.

### 2. Get an Anthropic API key

Go to https://console.anthropic.com/ and create an API key.

### 3. Install

```bash
git clone <this-repo> notion-agent
cd notion-agent
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

> First run downloads the `all-MiniLM-L6-v2` embedding model (~90 MB) to your
> Hugging Face cache. This is a one-time cost.

### 4. Configure

```bash
cp .env.example .env
# edit .env and paste in ANTHROPIC_API_KEY and NOTION_TOKEN
```

---

## Usage

### Build the index

Run this the first time, and whenever your workspace has changed meaningfully.

```bash
notion-agent index
```

You'll see per-page progress and a summary like:

```
Indexed 42 pages into 317 chunks.
Stored at: /Users/you/.notion_agent/index
```

### Ask a cross-page question

```bash
notion-agent ask "What are the top 3 risks for Project Phoenix based on my \
meeting notes from the last month and my saved articles on market trends?"
```

Claude will run several `search_workspace` calls under the hood, synthesise,
and cite the source pages. Example output:

```
Based on your meeting notes and saved market-trend articles, the top three
risks for Project Phoenix are:

1. Supply-chain concentration — two suppliers account for 78% of component
   volume (*Phoenix Supplier Review, 2026-03-14*).
2. Regulatory drift in the EU AI Act Phase 2, which affects the model-card
   disclosure requirements on the core product (*EU AI Act — March update*,
   *Phoenix Weekly 2026-04-02*).
3. Customer-acquisition cost rising in the enterprise segment, now ~1.6× the
   plan assumption (*Phoenix Q1 Retro*).
```

### Other one-shot questions

```bash
notion-agent ask "What's on my Prompt Engineering Principles page?"
notion-agent ask "Summarise what I've written about onboarding over the past month."
```

### Read or write a specific page

```bash
notion-agent read --page https://www.notion.so/My-Page-abcdef0123456789abcdef0123456789

notion-agent append \
  --page <page-id> \
  --heading "Next Steps" \
  --body "Ship v1 by Friday. Owner: Rahul. Blockers: none."
```

### Interactive chat

```bash
notion-agent chat
```

Example session:

```
Notion Agent — interactive mode. Ctrl-D or 'exit' to quit.

you > what are my notes on prompt engineering?
claude > You have three pages touching on prompt engineering:
         1. *Prompt Engineering Principles* — covers chain-of-thought, few-shot
            examples, and role priming.
         2. *Weekly notes 2026-03-22* — short reflection on system prompts.
         3. *Book notes: Designing ML Systems* — chapter 10 notes on evals.

you > exit
```

### Inspect the current index

```bash
notion-agent stats
```

---

## How it works, in more detail

1. **Crawl** — `indexer.py` walks every page via Notion's `/search` endpoint,
   recursively fetching block children and flattening the tree into
   markdown-ish text. Depth is capped at 3 to protect against pathological
   nesting.
2. **Chunk** — `vector_store.chunk_text` splits on paragraph boundaries with a
   character-windowed, overlapping scheme (~1800 chars, 300 overlap). Each
   chunk is prefixed with its page title so embeddings have topical context.
3. **Embed** — `sentence-transformers/all-MiniLM-L6-v2` produces L2-normalised
   384-dim vectors on CPU.
4. **Persist** — vectors saved as `embeddings.npy`, chunk metadata as
   `chunks.pkl`, manifest as JSON, all under `~/.notion_agent/index/`.
5. **Retrieve** — cosine similarity via normalised inner product
   (`embeddings @ query.T`). Fast enough for hundreds of thousands of chunks
   without FAISS.
6. **Agent loop** — `agent.py` hands Claude three tools and loops until
   `stop_reason == "end_turn"` or the turn budget is exhausted.

### Tools exposed to Claude

| Tool                                     | Purpose                                                         |
| ---------------------------------------- | --------------------------------------------------------------- |
| `read_page(page_id)`                     | Fetch a specific page's full content.                           |
| `search_workspace(query, top_k?)`        | Semantic search over the local vector index.                    |
| `append_section(page_id, heading, body?)`| Append an H2 section (with optional body) to a page.            |

The system prompt tells Claude to:

- Decompose multi-topic questions into multiple narrow searches.
- Cite every factual claim with the page title.
- Never hallucinate page IDs — search first.
- Only write when the user has given an explicit write instruction.
- Admit when the index has nothing relevant.

---

## Configuration reference

All settings are loaded from environment variables (or a `.env` file).

| Variable                   | Default                            | Purpose                                       |
| -------------------------- | ---------------------------------- | --------------------------------------------- |
| `ANTHROPIC_API_KEY`        | **required**                       | Your Anthropic API key.                       |
| `NOTION_TOKEN`             | **required**                       | Your Notion integration token.                |
| `CLAUDE_MODEL`             | `claude-opus-4-7`                  | Override the Claude model.                    |
| `EMBEDDING_MODEL`          | `all-MiniLM-L6-v2`                 | Override the sentence-transformers model.     |
| `NOTION_AGENT_INDEX_DIR`   | `~/.notion_agent/index`            | Where the local vector index is stored.       |

---

## Testing

```bash
pip install -e ".[dev]"
pytest
```

The unit tests cover the pure-logic bits (chunker, ID normaliser, block
renderer, Notion split helper) and don't require network access or API keys.

---

## Known limitations & ideas for next steps

- **Incremental re-indexing.** `index` currently rebuilds from scratch. Adding
  a `last_edited_time` cursor per page would make refreshes cheap.
- **Databases.** Database rows are pages, so they're crawled, but no special
  handling of database properties (status, dates, relations) — a
  `query_database` tool would add real power here.
- **Write surface.** Only `append_section` is exposed. Full block-tree
  mutation is possible via the underlying client but deliberately gated
  behind a simple primitive.
- **Conversation history in `chat`.** Each turn starts fresh. A simple
  rolling `messages` buffer would give true multi-turn memory.
- **MCP.** This project uses Notion's REST API via `notion-client`. The tool
  specs + dispatcher in `tools.py` would swap cleanly to an MCP transport
  when the Notion MCP server is worth depending on.

---

## License

MIT — see [LICENSE](LICENSE).

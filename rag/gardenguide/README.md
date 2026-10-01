# 🪴 GardenGuide — RAG-Powered Garden Wisdom

**Your own garden knowledge base, in your terminal.**  
Upload seed packets, planting guides, and garden journals. Ask questions. Get answers grounded in YOUR data.

```bash
gardenguide ingest tomato-seeds.pdf
gardenguide ask "When should I start tomatoes indoors?"
```

## ✨ Features

- 📥 **Ingest** — Add seed packets, extension-office PDFs, garden notes (`.txt`, `.md`, `.pdf`)
- 🔍 **Query** — Retrieve the most relevant passages from your garden docs
- 💬 **Ask** — Get natural-language answers generated from your own content, with source citations
- 🗂️ **Manage** — List, remove, or clear your document library
- 🔌 **API-free** — Uses your existing OpenAI key (or any OpenAI-compatible endpoint)

## 🚀 Quick Start

```bash
# Install
pip install -r requirements.txt

# Ingest your first document
python gardenguide.py ingest ~/gardening/tomato-guide.txt

# Ask questions
python gardenguide.py ask "How much sun do tomatoes need?"

# Just retrieve passages (no generation)
python gardenguide.py query "watering schedule"
```

## 📚 Commands

| Command | Description |
|---------|-------------|
| `ingest <file>` | Add a gardening document to the knowledge base |
| `ask <question>` | Ask a question, get an answer grounded in your docs |
| `query <question>` | Retrieve relevant passages (no generation) |
| `list` | Show all ingested documents |
| `remove <file>` | Remove a specific document |
| `clear` | Delete ALL ingested data |
| `info` | Show database statistics |

## ⚙️ Configuration

Set these environment variables (or they're read from `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | Your OpenAI API key |
| `GARDENGUIDE_DIR` | `~/.gardenguide` | Where documents and vectors are stored |
| `GARDENGUIDE_EMBED_MODEL` | `text-embedding-3-small` | Embedding model |
| `GARDENGUIDE_GEN_MODEL` | `gpt-4o-mini` | Generation model |

Use any OpenAI-compatible endpoint by setting `OPENAI_BASE_URL` together with `OPENAI_API_KEY`.

## 🏗️ Architecture

```
gardenguide.py      →  CLI entry point (Click)
src/doc_loader.py   →  Document loading, PDF parsing, sentence-boundary chunking
src/rag_engine.py   →  RAG pipeline: embed, retrieve, generate + vector store
~/.gardenguide/     →  Persistent vector store (JSON + numpy)
```

## 💡 Example

```bash
# Ingest seed packets and guides
gardenguide ingest tomato-seed-packet.txt
gardenguide ingest usda-planting-guide.pdf

# Ask a practical question
gardenguide ask "When should I plant tomatoes?"

# Output:
# Based on your USDA hardiness zone document and the
# tomato seed packet instructions, start seeds indoors
# 6-8 weeks before the last frost date. For your zone,
# that's mid-March. Transplant outdoors after the last
# frost (typically mid-May).
#
# Sources:
#   • /home/me/gardening/usda-planting-guide.pdf
#   • /home/me/gardening/tomato-seed-packet.txt
```

## 📋 Requirements

- Python 3.9+
- OpenAI API key (or compatible endpoint)

## 📄 License

MIT — use it, fork it, garden with it.
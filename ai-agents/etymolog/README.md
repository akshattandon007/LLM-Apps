# 📖 etymolog — The Word Journey Explorer

**Type any English word. Get its full journey through time.**

etymolog is a CLI tool that traces where words come from, how their meanings drifted over centuries, and which surprising cousin words you didn't know were related. Like a podcast host who only talks about etymology — but in your terminal.

## ✨ What It Does

- **Origin story** — Where did the word come from? Old English, Latin, Greek, Arabic, Proto-Indo-European?
- **Meaning drift** — How did "nice" go from "ignorant" to "pleasant"? etymolog shows the journey.
- **Word cousins** — Words in other languages that share the same root.
- **Similar & rhyming words** — Semantic neighbours and sound-alikes via Datamuse.
- **LLM-powered narrative** — Optional AI-generated story (via OpenRouter) that reads like a fascinating mini-podcast script.

## 🚀 Quick Start

```bash
# No install needed — just run
cd ai-agents/etymolog/
python3 etymolog.py serendipity

# Or with LLM narrative (needs OPENROUTER_API_KEY)
export OPENROUTER_API_KEY="sk-or-v1-..."
python3 etymolog.py serendipity

# Pipe mode
echo "serendipity" | python3 etymolog.py

# JSON output for scripting
python3 etymolog.py serendipity --json | jq '.etymology'
```

## 📋 Examples

```bash
# Basic etymology
python3 etymolog.py serendipity

# No LLM mode (just raw data)
python3 etymolog.py nice --no-llm

# Batch words
echo -e "serendipity\nnice\netymology" | while read w; do python3 etymolog.py "$w"; echo "---"; done
```

## 🔧 Requirements

- Python 3.8+
- No pip packages needed (stdlib only)
- Optional: `OPENROUTER_API_KEY` env var for LLM narrative

## 🔌 Data Sources

| Source | API | Auth | Use |
|--------|-----|------|-----|
| [Wiktionary](https://en.wiktionary.org) | MediaWiki parse + REST | None (free, CC-BY-SA) | Etymology text + definitions |
| [Datamuse](https://www.datamuse.com/api/) | `/words?ml=`, `/words?rel_rhy=` | None (free) | Similar words, rhymes, triggers |
| [OpenRouter](https://openrouter.ai) | Chat completions | API key (optional) | LLM narrative generation |

## 🧪 Tests

```bash
cd ai-agents/etymolog/
python3 -m unittest test_etymolog.py -v
```

Tests cover:
- API call formatting (mocked)
- Network failure recovery
- Fallback narrative generation
- Output formatting
- CLI argument handling

## ⚙️ Options

| Flag | Description |
|------|-------------|
| `--json` | Output as JSON for programmatic use |
| `--no-llm` | Skip LLM narrative, show raw data only |
| `-h` / `--help` | Show help |

## 🧠 How It Works

```
Your word ──► Wiktionary ──► Etymology + definitions
            ├─► Datamuse ──► Similar words + rhymes + triggers
            └─► [Optional] OpenRouter LLM ──► Narrative story
                    │
                    ▼
            Beautiful ASCII output
```

## 📁 Project Structure

```
etymolog/
├── etymolog.py        # Main CLI app
├── test_etymolog.py   # 12 unit tests
├── Decisions.md       # Architectural decisions (15 entries)
├── Flow.md            # Execution flow + dependency graph
└── README.md          # This file
```

## 📜 License

Data from Wiktionary is CC-BY-SA licensed. This tool is for educational and personal use.
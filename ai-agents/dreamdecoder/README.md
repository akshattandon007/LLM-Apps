# DreamDecoder

🌙 AI-powered dream journal with symbolic interpretation.

Record your dreams, get AI-powered interpretations, and discover patterns in your subconscious over time.

## Features

- **Log** dreams and receive instant symbolic analysis
- **Browse** your journal chronologically
- **Search** by keywords in dream text, symbols, or themes
- **Track** recurring symbols, moods, and themes over time
- **Zero API keys** — uses the configured Hermes LLM or a built-in symbolic interpreter

## Quick Start

```bash
# Record a dream
python main.py log "I was flying over mountains at sunset, then fell into the ocean"

# Browse your journal
python main.py list

# View details
python main.py view <entry-id>

# Search
python main.py search flying

# Dream insights
python main.py stats
```

## Requirements

- Python 3.10+
- Hermes CLI (`/opt/venv/bin/hermes`) — optional, fallback interpreter built-in
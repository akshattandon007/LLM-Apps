# 📞 Parallel Lives — Voice Calls with History

> *Real-time conversations with anyone from history or fiction.*

**Parallel Lives** lets you pick a character — Einstein, Cleopatra, Sherlock Holmes, Ada Lovelace, Joan of Arc — and have an in-character conversation. Each character has a unique personality, period-accurate knowledge, and memory of your conversation history.

## Characters

| Character | Era | Vibe |
|-----------|-----|------|
| 🧠 Albert Einstein | 1930s | *"The important thing is not to stop questioning."* |
| 👑 Cleopatra | 40 BC | *"A queen does not ask. She commands."* |
| 🔍 Sherlock Holmes | 1890s | *"Elementary, my dear user."* |
| 🌌 Ada Lovelace | 1840s | *"That brain of mine is something more than mortal."* |
| ⚔️ Joan of Arc | 1429 | *"I am not afraid. I was born to do this."* |

## Usage

```bash
# List available characters
python main.py --list

# Call a character
python main.py --call "einstein"

# Simulated conversation demo
python main.py --simulate
```

## Quick Start

```bash
pip install -r requirements.txt
python main.py --simulate
```

## Testing

```bash
pytest tests/ -v
```

## Project Files

| File | Purpose |
|------|---------|
| `Decisions.md` | Why every architectural choice was made |
| `Flow.md` | Execution trace through files and functions |
| `README.md` | Getting started guide |
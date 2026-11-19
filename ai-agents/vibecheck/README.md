# 🎭 VibeCheck — Communication Tone Analyzer

**Read the room before you hit send.**

VibeCheck analyzes any text for emotional tone, subtext, clarity, and communication style. Whether you're drafting an important email, crafting a sensitive Slack message, or just checking how your words might land — VibeCheck gives you the full read before you send.

## ✨ Features

- **Tone Analysis** — Detects overall tone, mood, confidence level, and formality
- **Subtext Detection** — Surfaces emotional undercurrents the reader might pick up on
- **Clarity Scoring** — Rates your message clarity from 1-10
- **Misinterpretation Warnings** — Flags ways your text could be misunderstood
- **Rewrite Suggestions** — Actionable improvements for different audiences
- **A/B Comparison** — Compare original vs rewritten versions side by side
- **Interactive Mode** — Chat-like REPL for quick checks
- **Pipe Support** — Works with `echo`, `cat`, and other Unix pipes

## 🚀 Installation

```bash
# Clone and install
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps/ai-agents/vibecheck
pip install -e .
```

## ⚙️ Setup

VibeCheck needs an LLM API key. By default it uses **OpenRouter** (free tier available):

```bash
# Option 1: Set environment variable
export OPENROUTER_API_KEY="your-key-here"

# Option 2: Save to config (persistent)
vibecheck --setup "your-key-here"
```

### Alternative providers

```bash
# OpenAI
export VIBECHECK_PROVIDER=openai
export OPENAI_API_KEY="sk-..."

# Ollama (local)
export VIBECHECK_PROVIDER=ollama
export VIBECHECK_MODEL=llama3
export OLLAMA_URL="http://localhost:11434/v1"
```

## 📖 Usage

### Quick analysis (inline)

```bash
vibecheck --text "Hey, did you finish that thing I asked about yesterday? Kinda urgent now."
```

### From a file

```bash
vibecheck --file draft-email.txt
```

### Pipe from another command

```bash
cat message.txt | vibecheck
```

### Compare original vs rewritten

```bash
vibecheck --compare --text "I need this done NOW. ||| I'd appreciate if you could prioritize this — the deadline is approaching."
```

### Interactive mode

```bash
vibecheck --interactive
```

Then type or paste text at the `vibecheck>` prompt. Use `/file path.txt` to analyze a file, or `/compare text ||| rewritten` to compare.

## 📊 Example Output

```
  Overall Tone:    Frustrated and urgent, expressing repeated unaddressed concerns
  Clarity Score:   7/10
  Confidence:      assertive
  Formality:       casual
  Detected Mood:   frustrated

  🎭 Emotional Subtext:
     • Frustration from being ignored
     • Anxiety about project deadline

  ✅ Key Strengths:
     • Clearly communicates the stakes
     • Shows investment in project success

  ⚠️  Potential Misinterpretations:
     • Could come across as aggressive or accusatory
     • May make recipients defensive

  💡 Rewrite Suggestions:
     • Start with a neutral observation rather than complaint
     • Use "I" statements instead of accusations
```

## 🧪 Running Tests

```bash
pip install -e ".[dev]"  # or: pip install pytest
pytest tests/ -v
```

## 🏗 Architecture

```
vibecheck/
├── __init__.py          # Package metadata
├── analyzer.py          # Core: LLM provider abstraction, analysis logic
├── cli.py               # CLI entry point (argparse + interactive REPL)
tests/
├── __init__.py
└── test_analyzer.py     # Unit tests with mock LLM provider
```

## 🔧 Tech Stack

- **Python 3.10+** — Core language
- **requests** — HTTP for LLM API calls
- **pytest** — Test framework
- **LLM providers**: OpenRouter (default), OpenAI-compatible, Ollama

## 📄 License

MIT
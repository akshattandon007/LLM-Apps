# StoryWeaver 🎭

**Interactive branching fiction — powered by AI.**

StoryWeaver is a CLI tool that generates immersive, branching interactive fiction stories. You provide a genre, setting, characters, and premise — the LLM writes the opening chapter with 3 choices, and your story unfolds dynamically from there.

## Features

- **🎭 Multiple genres** — Fantasy, sci-fi, mystery, horror, romance, adventure, and more
- **🌲 Branching narratives** — Every choice leads to a unique path
- **💾 Save & resume** — Stories are auto-saved; come back anytime
- **🔌 API-agnostic** — Works with any OpenAI-compatible API (OpenRouter, OpenAI, local LLMs)
- **📖 No account needed** — Just an LLM API key and you're writing stories

## Installation

```bash
# Clone the repo
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps/ai-agents/storyweaver

# Install dependencies
pip install -r requirements.txt

# Install the CLI (optional, for `storyweaver` command)
pip install -e .
```

## Usage

### Set your API key

```bash
export LLM_API_KEY="sk-or-v1-your-key-here"
```

### Start a new story (interactive)

```bash
storyweaver new
```

You'll be prompted for:
- **Story title** — What's your story called?
- **Genre** — Fantasy, sci-fi, mystery, horror, romance, adventure...
- **Setting** — Where does it take place?
- **Characters** — Who's in it?
- **Premise** — What's the starting hook?

### Start a new story (non-interactive)

```bash
storyweaver new \
  --title "Dragon's Peak" \
  --genre fantasy \
  --setting "The Misty Mountains" \
  --characters "Kael the ranger, a young dragon" \
  --premise "Kael discovers an injured dragon on a forbidden peak"
```

### Continue a saved story

```bash
storyweaver continue --story-id dragons-peak
```

### List all saved stories

```bash
storyweaver list
```

### Playing

After each chapter, you'll see 3 choices. Pick one:

```
Enter choice (1-3, 's' to save & quit):
```

- Enter a number (1, 2, or 3) to continue the story
- Enter `s` to save and exit — your progress is preserved

### Custom model / API

```bash
storyweaver new --model "anthropic/claude-3.5-sonnet" --temperature 1.0
storyweaver new --api-base "https://api.openai.com/v1" --model "gpt-4o"
```

## Examples

### Quick start (one-liner)

```bash
LLM_API_KEY="sk-..." storyweaver new --title "Neon Detective" --genre cyberpunk \
  --setting "Rain-soaked Night City, 2147" \
  --characters "Detective Nova, a rogue AI" \
  --premise "A murder case leads Nova into an underground AI network"
```

### Resuming a session from a full path

```bash
storyweaver continue --path ~/.storyweaver/saves/neon-detective.json
```

## Architecture

```
CLI (cli.py)  →  Engine (engine.py)  →  LLM API
                      ↓
              Models (models.py) ←→ JSON storage
```

- `cli.py` — Argparse-based CLI; handles new, continue, list commands
- `engine.py` — Prompt construction and API communication
- `models.py` — Data classes for StorySession, StoryNode, Choice
- `prompts.py` — System and user prompt templates
- `storage.py` — JSON serialization (built into models.py)

## Tests

```bash
cd ai-agents/storyweaver
pip install pytest
pytest tests/ -v
```

Tests cover:
- Model creation, serialization, and round-trip I/O
- Engine prompt construction and mocked API calls
- CLI argument parsing and user interaction
- Choice validation and session state management

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `LLM_API_KEY` | (required) | OpenAI-compatible API key |
| `--api-base` | `https://openrouter.ai/api/v1` | API base URL |
| `--model` | `openai/gpt-4o-mini` | Model name |
| `--max-tokens` | `2048` | Max tokens per chapter |
| `--temperature` | `0.9` | Creativity (0-2) |

## License

MIT

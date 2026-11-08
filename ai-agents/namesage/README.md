# NameSage

**AI-powered name analytics from your terminal.**

Enter any first name and get a rich profile: predicted age, gender probability, country-of-origin probabilities, rhyming words for wordplay, and an LLM-synthesized name profile with era vibes, famous namesakes, cultural associations, and sibling-name suggestions.

## How it works

NameSage queries four free, zero-auth APIs in parallel:

| API | What it returns |
|-----|----------------|
| [Agify.io](https://agify.io) | Predicted age based on name prevalence |
| [Genderize.io](https://genderize.io) | Gender probability |
| [Nationalize.io](https://nationalize.io) | Country probability distribution |
| [Datamuse](https://datamuse.com/api) | Rhyming words for wordplay |

If `OPENROUTER_API_KEY` is set, the raw data is passed to an LLM (via OpenRouter) which synthesizes a warm, clever name profile.

## Installation

```bash
# Clone or enter the project directory
cd ai-agents/namesage

# Install with pip (editable mode for development)
pip install -e ".[dev]"
```

## Usage

```bash
# Analyse a name
namesage alexandra

# Or use the --name flag
namesage --name jordan
```

### Sample output

NameSage prints colorized, paneled output showing:
- Predicted age with record count
- Gender with confidence percentage
- Country probabilities as a table
- Rhyming words
- LLM-generated name profile (if API key is set)

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | No | Enables LLM-generated name profiles via OpenRouter |

## Testing

```bash
# Run all tests
pytest tests/ -v
```

Tests use `pytest-httpx` to mock HTTP requests — no external APIs needed.

## Project structure

```
namesage/
├── namesage/
│   ├── __init__.py
│   ├── cli.py          # CLI entry point (argparse)
│   ├── api.py          # Agify/Genderize/Nationalize/Datamuse API wrappers
│   ├── llm.py          # OpenRouter LLM profile generation
│   └── formatter.py    # Rich-based ANSI terminal output
├── tests/
│   ├── __init__.py
│   ├── test_api.py     # API mock tests
│   └── test_formatter.py  # Formatter output tests
├── pyproject.toml
├── requirements.txt
├── README.md
├── Decisions.md        # Architectural decision record
└── Flow.md             # Execution trace and module dependency graph
```

## License

MIT
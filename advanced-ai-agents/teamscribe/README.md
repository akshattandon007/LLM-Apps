# TeamScribe 🗒️🤖

**Multi-agent meeting companion** — Turn raw meeting notes into structured summaries, decisions, action items, and follow-up emails using a team of 4 specialized AI agents working together.

```
Raw notes → [Transcriber] → [MinuteTaker] → [Scribe] → [Archivist] → Full meeting package
```

## What It Does

Ever left a meeting unsure of what was actually decided? TeamScribe takes your raw, messy meeting notes and runs them through a pipeline of 4 AI agents, each with a specific role:

| Agent | Role | Output |
|-------|------|--------|
| **Transcriber** 🧹 | Cleans up typos, filler, and disorganized notes | Structured, readable notes |
| **MinuteTaker** 📋 | Extracts decisions, action items, and key points | Structured data |
| **Scribe** ✍️ | Writes a professional summary and follow-up email | Ready-to-send output |
| **Archivist** 🗄️ | Archives decisions and detects trends over time | Historical record |

The agents collaborate through a shared `MeetingRecord` — each agent reads the previous agent's work and enriches it.

## Install

```bash
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps/advanced-ai-agents/teamscribe
pip install -r requirements.txt
```

## Usage

Set your OpenAI-compatible API key:

```bash
export OPENAI_API_KEY="sk-..."
# Optional: use a different model or base URL
export TEAMSCRIBE_MODEL="gpt-4o-mini"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
```

### Process meeting notes

```bash
python -m teamscribe process "Sprint Planning" \
  "Alice: Let's use Python for the backend... Bob: I'll handle tests by Friday" \
  --participants "Alice,Bob,Charlie" \
  --date "2026-11-09"
```

### Process from a file

```bash
MEETING_NOTES=$(cat examples/sample_meeting.txt)
python -m teamscribe process "Sprint Planning" "$MEETING_NOTES" --participants "Alice,Bob,Charlie"
```

### List saved meetings

```bash
python -m teamscribe list
```

### View a saved meeting

```bash
python -m teamscribe show ~/.teamscribe/meetings/2026-11-09--Sprint_Planning.json
```

## Example Output

After processing, you get:

- **Summary** — Professional 2-4 paragraph meeting summary
- **Decisions** — What was decided and why
- **Action Items** — Who does what by when
- **Follow-up Email** — Ready-to-send with subject line
- **Archive** — Decision history that builds across meetings

## Run Tests

```bash
python -m pytest tests/ -v
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | API key for LLM access |
| `OPENAI_BASE_URL` | OpenAI default | Custom endpoint (e.g. OpenRouter) |
| `TEAMSCRIBE_MODEL` | `gpt-4o-mini` | LLM model to use |
| `TEAMSCRIBE_OUTPUT` | `~/.teamscribe/meetings/` | Where meeting records are saved |
| `TEAMSCRIBE_ARCHIVE` | `~/.teamscribe/archive.json` | Where the cross-meeting archive lives |

## Tech Stack

- **Python 3.10+** with `openai` library
- **No external storage** — everything is local JSON files
- **No external APIs** — only the LLM API is needed

## Project Structure

```
teamscribe/
├── teamscribe/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── transcriber.py
│   │   ├── minute_taker.py
│   │   ├── scribe.py
│   │   └── archivist.py
│   ├── __init__.py
│   ├── __main__.py
│   ├── agent_base.py
│   ├── cli.py
│   ├── models.py
│   ├── orchestrator.py
│   └── storage.py
├── tests/
├── examples/
├── requirements.txt
├── Decisions.md
└── Flow.md
```

## License

MIT
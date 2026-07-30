# SketchIt Backend

A small Flask server that acts as a secure proxy between the SketchIt browser extension and the Anthropic Claude API.

## Why a separate backend?

Chrome extensions can't securely hold API keys — anything you ship with the extension is effectively public. Running a tiny local server means:

- Your API key stays on your machine
- You can swap models or tune the system prompt without republishing the extension
- The backend can be reused by other clients (CLI, VS Code extension, etc.)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

python server.py
```

The server listens on `http://127.0.0.1:5174` by default.

## Endpoints

### `GET /health`

Health check. Returns JSON:

```json
{
  "status": "ok",
  "model": "claude-opus-4-5",
  "api_key_configured": true
}
```

### `POST /chat`

The main endpoint. Request body:

```json
{
  "prompt": "Make the form blue and modern",
  "page_html": "<!DOCTYPE html>...",
  "page_url": "https://example.com",
  "history": [
    { "role": "user", "content": "…" },
    { "role": "assistant", "content": "…" }
  ]
}
```

Response body:

```json
{
  "explanation": "Applied a cobalt palette with generous whitespace…",
  "operations": [
    { "type": "load_font", "href": "https://fonts.googleapis.com/..." },
    { "type": "inject_css", "css": ":root { ... }" }
  ]
}
```

See [`../docs/OPERATIONS.md`](../docs/OPERATIONS.md) for the full operation schema.

## Configuration

All config is via environment variables. See [`.env.example`](.env.example).

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Your API key from console.anthropic.com |
| `SKETCHIT_MODEL` | `claude-opus-4-5` | Model name |
| `SKETCHIT_PORT` | `5174` | HTTP port |

## Development

The server is a single file — `server.py` — deliberately kept simple. The system prompt lives in-line at the top (`DESIGNER_SYSTEM_PROMPT`); tweak it and restart.

### Running tests

```bash
pip install pytest requests
pytest
```

(Tests are in the root `tests/` directory if added.)

### Logging

Set `FLASK_ENV=development` for verbose logs. All requests are logged with the prompt (truncated) and response shape.

## Troubleshooting

**"Model did not return valid JSON"** — Occasionally the model wraps its output in code fences despite the system prompt. The server strips fences defensively; if you still hit this, check the `raw` field in the error response for what came back.

**Slow first response** — Model cold-starts can take a few seconds. Subsequent requests are faster.

**Port already in use** — Set `SKETCHIT_PORT` to something else, and update the extension's `manifest.json` + `content.js` + `popup.js` to match.

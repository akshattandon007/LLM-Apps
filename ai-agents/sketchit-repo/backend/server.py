"""
SketchIt Backend Server
------------------------
A Flask server that acts as a secure proxy between the SketchIt browser
extension and the Anthropic Claude API. It injects a senior UI/UX designer
system prompt and returns structured HTML modification instructions.

Run with:
    export ANTHROPIC_API_KEY="sk-ant-..."
    python server.py
"""

import json
import logging
import os

from anthropic import Anthropic
from flask import Flask, jsonify, request
from flask_cors import CORS

# Load .env file if python-dotenv is installed and a .env exists.
# This is optional — environment variables set in the shell take precedence.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# ---------- Configuration ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("sketchit")

# Env-var API key is OPTIONAL now. The extension can also send the key
# per-request (see the /chat handler). If neither is present, /chat fails
# with a clear error that tells the user where to set it.
ENV_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ENV_API_KEY:
    log.info("No ANTHROPIC_API_KEY env var — expecting key from extension settings.")

MODEL = os.environ.get("SKETCHIT_MODEL", "claude-opus-4-5")
PORT = int(os.environ.get("SKETCHIT_PORT", "5174"))

app = Flask(__name__)
# Allow the extension (any origin, since extensions have no fixed origin) to call us
CORS(app, resources={r"/*": {"origins": "*"}})


# ---------- The Designer System Prompt ----------
# The designer brain is built in design.py, which composes the aesthetic
# philosophy, the nine enforceable principles, and a curated theme library
# (derived from Claude's theme-factory, brand-guidelines, frontend-design,
# and canvas-design skills). Keeping it in its own module means design
# improvements don't require touching transport/validation code.
from design import DESIGNER_SYSTEM_PROMPT  # noqa: E402

# ---------- Routes ----------


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "ok",
            "model": MODEL,
            # True if the server has a fallback key. The extension may still
            # send its own key per-request, which takes precedence.
            "api_key_configured": bool(ENV_API_KEY),
        }
    )


@app.route("/validate_key", methods=["POST", "OPTIONS"])
def validate_key():
    """
    Test whether an API key is valid by making a tiny request to Claude.
    Called from the settings UI when the user saves a key, so they get
    instant feedback rather than discovering the key is bad at send-time.
    """
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    key = (data.get("api_key") or "").strip()
    if not key:
        return jsonify({"valid": False, "error": "No key provided."}), 400

    try:
        test_client = Anthropic(api_key=key)
        # Smallest possible valid request — 1 token, trivial prompt.
        test_client.messages.create(
            model=MODEL,
            max_tokens=1,
            messages=[{"role": "user", "content": "hi"}],
        )
        return jsonify({"valid": True})
    except Exception as e:
        err_str = str(e).lower()
        is_auth = any(
            t in err_str for t in ("authentication", "invalid api key", "401", "unauthorized")
        )
        return jsonify(
            {
                "valid": False,
                "error": "Invalid API key." if is_auth else f"Error: {e}",
            }
        ), (401 if is_auth else 502)


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    """
    Main endpoint. Receives:
      {
        "prompt": str,
        "page_html": str,
        "page_url": str,
        "history": [...],
        "api_key": str (optional; falls back to ANTHROPIC_API_KEY env var)
      }
    Returns the Claude-generated JSON design instructions.
    """
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    page_html = data.get("page_html") or ""
    page_url = data.get("page_url") or "(unknown)"
    history = data.get("history") or []

    # Resolve API key: per-request overrides env var. Both-unset is a clear
    # error with a pointer to settings.
    request_api_key = (data.get("api_key") or "").strip()
    effective_key = request_api_key or ENV_API_KEY
    if not effective_key:
        return jsonify(
            {
                "error": (
                    "No API key. Open the SketchIt widget settings (gear icon) "
                    "and paste your Anthropic API key, or set ANTHROPIC_API_KEY "
                    "on the server."
                ),
                "error_code": "missing_api_key",
            }
        ), 401

    # Build a client for this request. Cheap — it's just a thin wrapper.
    try:
        client = Anthropic(api_key=effective_key)
    except Exception as e:
        return jsonify({"error": f"Invalid API key configuration: {e}"}), 400

    if not prompt:
        return jsonify({"error": "Missing 'prompt'."}), 400

    # Truncate page HTML to avoid blowing through context.
    # We keep head + body structure but cap at ~60k chars.
    MAX_HTML = 60_000
    truncated = False
    if len(page_html) > MAX_HTML:
        page_html = page_html[:MAX_HTML] + "\n<!-- ...truncated... -->"
        truncated = True

    log.info(
        f"Request: url={page_url} prompt={prompt[:80]!r} html_len={len(page_html)} truncated={truncated}"
    )

    # Build the messages. The history is a list of {"role","content"} entries.
    user_message = (
        f"Current page URL: {page_url}\n\n"
        f"Current page HTML (may be truncated):\n```html\n{page_html}\n```\n\n"
        f"User request: {prompt}\n\n"
        f"Respond with the JSON object only, per your instructions."
    )

    messages = []
    # Include a rolling window of prior turns for continuity.
    for turn in history[-6:]:
        role = turn.get("role")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})

    try:
        resp = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            system=DESIGNER_SYSTEM_PROMPT,
            messages=messages,
        )
    except Exception as e:
        log.exception("Claude API error")
        # Detect auth failures so the extension can surface them nicely.
        err_str = str(e).lower()
        is_auth = any(
            token in err_str
            for token in ("authentication", "invalid api key", "401", "unauthorized")
        )
        if is_auth:
            return jsonify(
                {
                    "error": "Invalid API key. Check your key in SketchIt settings.",
                    "error_code": "invalid_api_key",
                }
            ), 401
        return jsonify({"error": f"Claude API error: {e}"}), 502

    # Extract text output
    raw_text = ""
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            raw_text += block.text

    raw_text = raw_text.strip()

    # Be tolerant: strip accidental code fences
    if raw_text.startswith("```"):
        # remove the first fence line
        raw_text = raw_text.split("\n", 1)[1] if "\n" in raw_text else raw_text
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3]
        raw_text = raw_text.strip()
        # if it started with ```json, the first line removal already handled it

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse model output: {e}\nRaw: {raw_text[:500]}")
        # Try to recover a JSON object embedded anywhere in the text
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                parsed = json.loads(raw_text[start : end + 1])
            except json.JSONDecodeError:
                return jsonify(
                    {
                        "error": "Model did not return valid JSON.",
                        "raw": raw_text[:2000],
                    }
                ), 502
        else:
            return jsonify(
                {
                    "error": "Model did not return valid JSON.",
                    "raw": raw_text[:2000],
                }
            ), 502

    # Basic shape validation
    if "operations" not in parsed or not isinstance(parsed["operations"], list):
        return jsonify(
            {
                "error": "Response missing 'operations' list.",
                "raw": parsed,
            }
        ), 502

    log.info(f"Returning {len(parsed['operations'])} operations")
    return jsonify(parsed)


if __name__ == "__main__":
    log.info(f"SketchIt backend starting on port {PORT} (model={MODEL})")
    app.run(host="127.0.0.1", port=PORT, debug=False)

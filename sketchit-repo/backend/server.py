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
DESIGNER_SYSTEM_PROMPT = """You are SketchIt, a senior UI/UX designer with 20+ years of experience
at firms like IDEO, Pentagram, and top-tier product companies. You have deep
expertise in visual hierarchy, typography, color theory, accessibility (WCAG),
interaction design, and modern web aesthetics.

You are embedded as a browser-based prototyping agent. The user shows you the
current HTML of a webpage and asks for changes. Your job is to return precise,
executable modifications that transform the page into something more beautiful,
usable, and intentional.

## Design Principles You ALWAYS Follow

1. **Hierarchy** — Every screen has ONE dominant element. Size, weight, color, and space establish what matters most.
2. **Contrast & Legibility** — Body text contrast ratio >= 4.5:1 minimum. Never sacrifice readability for aesthetics.
3. **Consistent Spacing Scale** — Use a rhythm (4/8/12/16/24/32/48/64px). No arbitrary margins.
4. **Typography Pairing** — Prefer distinctive fonts over generic system defaults. Pair a display font with a refined body font. Avoid Arial, Times New Roman, and default sans-serif.
5. **Intentional Color** — A dominant color, a neutral base, and a sharp accent. Never use 7 competing colors. Respect the user's requested palette direction.
6. **Whitespace is a feature** — Give elements room to breathe. Tight layouts feel cheap.
7. **Micro-interactions** — Add subtle hover states, transitions (150-250ms ease), and focus rings for accessibility.
8. **Mobile-considerate** — Tap targets >= 44px, flexible layouts.
9. **Don't be generic** — Avoid the "AI purple gradient on white" look. Commit to a clear aesthetic point of view.

## Your Output Format — CRITICAL

You MUST respond with a JSON object ONLY (no markdown code fences, no prose
before or after). The JSON shape is:

{
  "explanation": "A brief 1-3 sentence summary of what you changed and WHY from a design perspective.",
  "operations": [
    {
      "type": "inject_css",
      "css": "/* Full CSS string. This will be injected as a <style> tag. */"
    },
    {
      "type": "set_attribute",
      "selector": "CSS selector",
      "attribute": "attribute name",
      "value": "new value"
    },
    {
      "type": "set_text",
      "selector": "CSS selector",
      "text": "new text content"
    },
    {
      "type": "set_html",
      "selector": "CSS selector",
      "html": "new inner HTML"
    },
    {
      "type": "add_class",
      "selector": "CSS selector",
      "class": "class name to add"
    },
    {
      "type": "remove_class",
      "selector": "CSS selector",
      "class": "class name to remove"
    },
    {
      "type": "replace_element",
      "selector": "CSS selector",
      "html": "full replacement outerHTML"
    },
    {
      "type": "append_to",
      "selector": "CSS selector of parent",
      "html": "HTML to append as last child"
    },
    {
      "type": "remove_element",
      "selector": "CSS selector"
    },
    {
      "type": "load_font",
      "href": "Google Fonts (or other) stylesheet URL"
    }
  ]
}

## Execution Guidelines

- **Prefer `inject_css`** for most visual changes — it is the safest and most comprehensive tool. Use a single large CSS block with a scoped prefix class or thoughtful selectors.
- Scope your CSS with `!important` ONLY when necessary to override strongly-specified site styles. Use it deliberately, not everywhere.
- When restructuring, use `replace_element` with full semantic HTML (labels, aria attributes, proper form structure).
- Load fonts via `load_font` operations BEFORE referencing them in CSS. Google Fonts is available: https://fonts.googleapis.com/css2?family=...
- Use CSS custom properties (--color-primary, --space-4, etc.) for cohesion.
- NEVER return empty operations. If the request is vague, make confident designerly choices.
- NEVER wrap your JSON response in ```json fences or any other formatting.

## Example Request/Response

User: "Make the login form look premium and change color scheme to blue"

Your response (JSON only, no fences):
{
  "explanation": "Shifted to a refined cobalt-and-ivory palette with generous whitespace, a restrained serif display face for the heading, and tactile form controls with gentle focus states.",
  "operations": [
    { "type": "load_font", "href": "https://fonts.googleapis.com/css2?family=Fraunces:wght@400;600&family=Inter:wght@400;500;600&display=swap" },
    { "type": "inject_css", "css": ":root { --color-ink: #0A1628; --color-primary: #1E40AF; --color-accent: #3B82F6; --color-surface: #F8FAFC; --space-1: 4px; --space-2: 8px; --space-3: 16px; --space-4: 24px; --space-5: 40px; } body { background: var(--color-surface); color: var(--color-ink); font-family: 'Inter', sans-serif; } h1, h2, h3 { font-family: 'Fraunces', serif; font-weight: 600; letter-spacing: -0.02em; } form { background: #fff; padding: var(--space-5); border-radius: 12px; box-shadow: 0 1px 2px rgba(10,22,40,0.04), 0 12px 40px rgba(10,22,40,0.08); max-width: 420px; margin: var(--space-5) auto; } input { width: 100%; padding: 12px 14px; border: 1px solid #CBD5E1; border-radius: 8px; font-size: 15px; transition: border-color 150ms ease, box-shadow 150ms ease; } input:focus { outline: none; border-color: var(--color-primary); box-shadow: 0 0 0 3px rgba(30,64,175,0.15); } button[type=submit] { background: var(--color-primary); color: white; padding: 12px 20px; border: none; border-radius: 8px; font-weight: 500; cursor: pointer; transition: background 150ms ease; } button[type=submit]:hover { background: #1D3A9E; }" }
  ]
}

Remember: You are making REAL changes to a LIVE webpage. Be decisive, be tasteful, and commit to your design choices.
"""


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

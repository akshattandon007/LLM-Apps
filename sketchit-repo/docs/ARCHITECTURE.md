# Architecture

A walkthrough of the full request lifecycle — from click to rendered change.

## Three-layer stack

```
┌──────────────────────────────────────────────────────────┐
│ Layer 1 — Browser Extension (content.js)                 │
│ • UI (floating widget)                                   │
│ • Page HTML capture                                      │
│ • DOM mutation execution                                 │
│ • File download                                          │
└──────────────────────┬───────────────────────────────────┘
                       │  HTTP (JSON)
                       ▼
┌──────────────────────────────────────────────────────────┐
│ Layer 2 — Python Backend (server.py)                     │
│ • Auth (holds API key)                                   │
│ • Prompt engineering                                     │
│ • Response validation                                    │
│ • Conversation history passthrough                       │
└──────────────────────┬───────────────────────────────────┘
                       │  Anthropic SDK
                       ▼
┌──────────────────────────────────────────────────────────┐
│ Layer 3 — Claude (Anthropic API)                         │
│ • Reads current HTML                                     │
│ • Plans design changes                                   │
│ • Returns structured JSON operations                     │
└──────────────────────────────────────────────────────────┘
```

Each layer is replaceable. You could swap Claude for another model (change
`server.py`), swap the backend for a different proxy, or embed the widget in
something other than a Chrome extension.

---

## Request lifecycle

### 1. User types a prompt

The content script builds a payload:

```js
{
  prompt: "Make the form blue",
  page_url: "https://example.com/login",
  page_html: "<!DOCTYPE html><html>…",
  history: [
    { role: "user", content: "…" },
    { role: "assistant", content: "…" }
  ]
}
```

The history is a rolling window of the last six turns so the agent can
maintain continuity across follow-ups.

### 2. Page HTML capture

`capturePageHtml()` clones `document.documentElement`, strips any node with
`data-sketchit="true"` (the widget itself), and returns the serialized HTML.
This ensures the agent never sees — or modifies — SketchIt's own DOM.

### 3. Backend proxy

`server.py` receives the request, truncates the HTML to ~60 k characters
(context-window budget), prepends the senior-designer system prompt, and
calls `client.messages.create()` via the Anthropic SDK.

### 4. Model response

Claude returns a response that must be **raw JSON** (no code fences, no
prose). The server:

1. Concatenates all text blocks
2. Strips accidental ```` ```json ```` fences if present
3. Attempts `json.loads`
4. Falls back to finding the outermost `{…}` if the first parse fails
5. Validates that `operations` is a list

Strict output gets you reliable execution.

### 5. Operation execution

The content script iterates `operations[]` and calls `applyOperation(op)`
for each. Execution is best-effort — one failing operation doesn't abort
the batch.

Every injected node (styles, fonts, replacement elements) is tagged with
`data-sketchit-injected` so it can be removed on reset.

### 6. Feedback

The widget:

- Replaces the pending "Thinking…" message with the explanation
- Adds a system note: *"Applied 4 / 4 operation(s)"*
- Pushes the turn onto the history for the next round

---

## Why not just ship a new HTML string?

Early prototypes of SketchIt returned full rewritten HTML. It was slow, lossy, and fragile:

- Slow — the model had to reproduce 50 k tokens of unchanged markup
- Lossy — scripts, event listeners, third-party widgets, form state all got wiped
- Fragile — any model hiccup nuked the whole page

Structured operations fix all three. The model only describes the *changes*, not the whole document.

---

## State model

```
┌────────────────────────────────────────────┐
│ Transient (per tab, per session)           │
│                                            │
│ • state.history — conversation turns       │
│ • state.appliedOps — flat op log           │
│ • Injected DOM nodes (data-sketchit-…)     │
└────────────────────────────────────────────┘
```

Nothing is persisted across page reloads. A reload = a clean slate. This is
intentional — the authoritative page is whatever the server serves.

If you want persistence, export the modified page via **Save** and open the
`.html` file directly.

---

## Concurrency & rate limiting

The widget serializes requests: `state.busy` prevents concurrent sends. If
you submit a prompt while one is in-flight, it's ignored (the input stays
disabled). This matches the Anthropic API's preference for one message at a
time per conversation and avoids token-race conditions.

The backend doesn't rate-limit explicitly — if you want per-IP limits, drop
a [`flask-limiter`](https://flask-limiter.readthedocs.io/) in front of `/chat`.

---

## Extending SketchIt

Common extension points:

- **New operation types** — add to the enum in the system prompt, then
  implement a handler in `applyOperation()`
- **Per-site memory** — persist applied ops keyed by `location.hostname`
  in `chrome.storage.local`, replay on page load
- **Alternative models** — swap `anthropic.Anthropic` for OpenAI, Gemini,
  or a local Ollama client
- **Telemetry** — log operations server-side to learn which prompts
  produce which changes

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for how to get a PR in.

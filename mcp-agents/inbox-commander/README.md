# 📥 Inbox Commander

**Your inbox, triaged to zero — threads summarized, replies drafted in your voice, nothing sent without a nod.**

```text
"Summarize the vendor thread and draft a reply declining the renewal
 but offering to reconnect in Q1."
```

Inbox Commander is a **Gmail MCP agent** that turns your inbox into a natural-language conversation. Search, read, summarize, draft, label, archive — all from plain English. It exposes the full triage loop as MCP tools, so any MCP-capable host (Hermes, Claude Desktop, or your own client) can drive your Gmail.

---

## 🧰 What it does

| Capability | How |
|---|---|
| 🔍 **Search** | `search_threads` — Gmail search syntax, returns thread summaries |
| 📖 **Read** | `read_thread` — full thread with all messages and extracted bodies |
| 🧠 **Summarize** | `summarize_thread` — AI summary (decisions, action items, next steps) |
| ✍️ **Draft** | `draft_reply` — AI reply in your voice, pick a tone |
| ✅ **Approve** | `approve_send` — explicit approval, returns a one-time token |
| 📤 **Send (gated)** | `send_draft` — only sends with a valid approval token |
| 🏷️ **Label** | `label_thread` — apply a label, created if missing |
| 📦 **Archive** | `archive_thread` — remove from INBOX, inbox zero achieved |

**Tones available:** `professional` (default), `friendly`, `concise`, `assertive`.

---

## 🔒 The Safety Gate

**Nothing is ever sent without your approval.** MCP tools can't pop a dialog, so the gate is enforced as a two-step protocol:

1. `draft_reply(thread_id, tone)` → returns a draft body for you to review.
2. `approve_send(thread_id, body)` → you approve the **exact** body, get a one-time `approval_token`.
3. `send_draft(thread_id, body, approval_token)` → only sends if the token matches the body. Wrong token, mismatched body, or a reused token? **Refused.**

The full flow:

```
🔍 search_threads(query="from:vendor.example")
📖 read_thread(thread_id="...")
🧠 summarize_thread(thread_id="...")
✍️ draft_reply(thread_id="...", tone="professional")   # show user; user approves
✅ approve_send(thread_id="...", body="<approved body>")  # → approval_token
📤 send_draft(thread_id="...", body="<approved body>", approval_token="...")
🏷️ label_thread(thread_id="...", label="Vendors")
📦 archive_thread(thread_id="...")
```

---

## 🚀 Quick Start

### 1. Google Cloud OAuth

1. Create a project at [console.cloud.google.com](https://console.cloud.google.com) and enable the **Gmail API**.
2. **APIs & Services > Credentials > Create Credentials > OAuth client ID**, application type **Desktop app**. Download `credentials.json` into the project root.
3. Generate a refresh token (one-time, interactive):

```bash
python -m src.auth
```

This saves `token.json` (gitignored). Or skip the interactive flow and put the three values straight into `.env`.

### 2. Configure

```bash
cp .env.example .env
# fill in GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN, ANTHROPIC_API_KEY
```

`token.json` / `.env` / `credentials.json` are all gitignored — never commit them.

### 3. Install

```bash
python3 -m venv /tmp/inbox-commander-venv
/tmp/inbox-commander-venv/bin/pip install -r requirements.txt
```

### 4. Run

MCP stdio mode (default):

```bash
/tmp/inbox-commander-venv/bin/python main.py
```

Register with Hermes:

```bash
hermes mcp add inbox-commander -- /tmp/inbox-commander-venv/bin/python /data/LLM-Apps/mcp-agents/inbox-commander/main.py
```

Optional FastAPI/HTTP mode (MCP over Streamable HTTP at `/mcp`, health at `/health`):

```bash
/tmp/inbox-commander-venv/bin/python main.py --http --port 8000
```

---

## 🏗️ Architecture

```
main.py                  MCP server entry (stdio by default, --http optional)
src/auth.py              OAuth 2.0 token management (env or interactive flow)
src/gmail_client.py      Gmail API wrapper: search/read/send/label/archive
src/summarizer.py        Claude summarization (+ deterministic fallback)
src/drafter.py           Claude tone-aware drafting (+ fallback templates)
src/tools.py             MCP tool definitions + the send-approval gate
src/models.py            Pydantic models
tests/test_smoke.py      Smoke tests with mocked Gmail + LLM (no credentials)
```

Without `ANTHROPIC_API_KEY`, summarization and drafting degrade to deterministic extractive/template output — the tools stay usable for tests and demo mode.

---

## 🧪 Tests

```bash
/tmp/inbox-commander-venv/bin/python tests/test_smoke.py
```

All tests mock the Gmail client and the LLM — no real credentials or network required. They verify the full tool surface including the send gate (no approval → rejected, mismatch → rejected, token reuse → rejected).

---

## 💬 Example queries

| You say | It does |
|---|---|
| *"Summarize the vendor thread and draft a reply declining the renewal"* | 🧠 Summarizes, then ✍️ drafts a decline in professional tone |
| *"What's in my inbox today?"* | 🔍 Searches INBOX, returns thread summaries |
| *"Read the thread about the Q4 budget"* | 📖 Fetches full thread with all messages |
| *"Draft a friendly reply to the party invite"* | ✍️ Drafts a casual, warm reply |
| *"Archive everything from the newsletter"* | 🔍 Finds newsletters, then 📦 archives them |
| *"Label the onboarding thread as 'Setup'"* | 🏷️ Applies/creates the label |

---

## 🛡️ Safety notes

- Nothing is ever sent without a valid `approve_send` token matching the exact body.
- Drafts are drafts — the user reviews before any token is created.
- AI summary/draft failures degrade to fallbacks — they never block reads.
- No credentials are ever committed to the repo.
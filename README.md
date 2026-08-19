<div align="center">

# 🧠 LLM Apps
### AI Agent, MCP Agent & RAG projects you can clone and run
**AI Agents · MCP Agents · RAG ·**
**Works with Claude · Gemini · OpenAI**

[![License](https://img.shields.io/github/license/akshattandon007/LLM-Apps?style=flat-square&color=blue)](./LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/akshattandon007/LLM-Apps?style=flat-square&color=orange)](https://github.com/akshattandon007/LLM-Apps/commits/main)
[![Stars](https://img.shields.io/github/stars/akshattandon007/LLM-Apps?style=flat-square&color=yellow)](https://github.com/akshattandon007/LLM-Apps/stargazers)
[![Issues](https://img.shields.io/github/issues/akshattandon007/LLM-Apps?style=flat-square&color=red)](https://github.com/akshattandon007/LLM-Apps/issues)

[![🚀 Quick Start](https://img.shields.io/badge/%F0%9F%9A%80_Quick_Start-2a2a2a?style=for-the-badge)](#-getting-started)
[![📂 Browse Projects](https://img.shields.io/badge/%F0%9F%93%82_Browse_Projects-2a2a2a?style=for-the-badge)](#-ai-agents)

</div>

---

A personal collection of **LLM-powered apps, AI Agents, MCP Agents, RAG
projects, and Browser Extensions** built with Claude, Gemini, and open-source
models. Each folder is a self-contained project with its own README and setup
instructions.

The repository is organised by what the agent *does* — prompt engineering,
retrieval, browsing, multimodal generation — rather than by the model
underneath, because most of these swap models freely.

---

## 📚 Table of Content

- [🤖 AI Agents](#-ai-agents)
- [🤖 🤖 Advanced AI Agents](#-advanced-ai-agent)
- [🔌 MCP Agents](#-mcp-agents)
- [📀 RAG (Retrieval Augmented Generation)](#-rag-retrieval-augmented-generation)
- [🚀 Getting Started](#-getting-started)

---

## 🤖 AI Agents

Single-purpose agents that use an LLM plus tools to complete a focused task.

- [✍️ Prompt Engineering Agent / Prompt Library](./ai-agents/AI-prompt-library-promptstar-claude%20-opus-4.6) — a curated prompt library and prompt-authoring helper
- [🅿️ Car-Park Agent](./ai-agents/Car-Park-agent%20Gemini%203.1%20Pro) — multimodal browser/vision agent on Gemini 3.1 Pro.
- [😂 Meme Agent](./ai-agents/meme-agent%20-%20Google%20gemma) — meme-generation agent powered by Google Gemma.
- [🎙️ Book to Podcast](./ai-agents/Book-to-pocast) — turns a book or long-form text into a conversational podcast episode.
- [🎓 Tutorial Builder Agent](./ai-agents/tutorial-builder-agent-Claude-Opus-4.6) — generates structured, multi-section tutorials from a topic or source material
- [🍸 BartenderAI Agent](./ai-agents/bartender-ai) — an AI bartender that finds trending cocktails for your location and season
- [🏡 Proppy — AI Real Estate Agent](./ai-agents/proppy-repo) — a Chrome extension that floats an animated koala on every webpage 
- [🧵 regex-please](./ai-agents/regex-please) — natural language → regex with live ANSI-highlighted matches in the terminal
- [🧶 Stash](./ai-agents/stash) — tick the craft supplies you own, get project ideas that use them. Warm web UI, no signup.
- [🎯 Procrastination Bingo](./ai-agents/procrastination-bingo) — 5x5 bingo board of tiny tasks. Get bingo in 10 minutes and celebrate with confetti.
- [🚗 Road Trip Quest](./ai-agents/road-trip-quest) — turn every family drive into a live storytelling adventure with chapters, challenges, and trivia
- [👵 Grandma's Voice](./ai-agents/grandmas-voice) — record a loved one's voice and generate bedtime stories narrated by them
- [🐾 What's My Pet Thinking?](./ai-agents/whats-my-pet-thinking) — describe your pet's weird behavior, get their hilarious inner monologue
- [🎁 The Gift](./ai-agents/the-gift) — describe someone you love, get a personalized gift idea + poem that shows you actually know them
- [📜 Myth](./ai-agents/myth) — fake Wikipedia articles about your friends. Pick an era, get an infobox, dubious citations, and a legacy they don't deserve.
- [🎭 TextPersona](./ai-agents/text-persona) — type a message, pick a persona (Yoda, Pirate, Shakespeare…), and the AI rewrites it in character
- [🎙️ VoiceVault](./ai-agents/voice-vault) — record loved ones' voices, ask them anything, get answers in their voice — an interactive audio keepsake

---
## 🤖 🤖 Advanced AI Agents

Agent orchestration.

- [👁️ ARGUS](./advanced-ai-agents/argus) — deep research agent. Generate sub-questions, crawl 4 sources, cross-reference, and deliver cited reports.
- [📊 AlphaBrief](./advanced-ai-agents/alphabrief) — financial intelligence multi-agent system. Portfolio tracking, technical analysis, SEC filings, sentiment, risk metrics, daily briefing.
- [🎧 Gesture DJ](./advanced-ai-agents/gesture-dj) - camera-powered music agent that reads the room and adapts the vibe in real-time 
- [🛡️ Icarus](./advanced-ai-agents/icarus) — incident remediation agent. Your SRE on autopilot: alert → triage → RCA → fix → post-mortem.
- [🎵 Mood agent](./advanced-ai-agents/spotify-mood-agent) - mood predicting agent using Spotify music listening habits 
- [🔁 PR Auto-Pilot](./advanced-ai-agents/pr-auto-pilot) — end-to-end PR review agent. Review diffs, patch bugs, run tests, and post reports.
- [🛍️ Shopping agent](./advanced-ai-agents/cheap-shopping-agent) - shopping agent that gets you the best deals
- [🔨 TraceForge](./advanced-ai-agents/traceforge) - self-improving agent loop: capture traces, curate good runs, extract reusable skills

---

## 🔌 MCP Agents

Agents that talk to external services (Notion, browsers, etc.) over the
**Model Context Protocol** pattern — i.e. LLM + a well-defined tool surface
that maps to a real-world system. Each agent here exposes a small, opinionated
toolset to Claude and runs an agent loop with citations and auditable writes.

- [📑 Notion Agent](./mcp-agents/notion-agent) — Claude Opus 4.7 agent that crawls a Notion workspace, maintains a local vector index, and answers cross-page questions with page citations. Also reads specific pages and appends sections. CLI-first. Fixes the "Notion Q&A doesn't know your workspace" complaint with proper retrieval.
- [♾️ Browser MCP Agent](./mcp-agents/browser-mcp-agent) — agent that drives a real browser over MCP. Navigates pages, extracts content, and completes goal-directed browsing tasks via a well-defined tool surface.
- [🎨 Figma MCP Agent](./mcp-agents/figma-agent) — design files ↔ code. Extract specs, export assets, style tokens.
- [📥 Inbox Commander](./mcp-agents/inbox-commander) — Gmail MCP agent — triage your inbox to zero. Summarize threads, draft replies, gate sends.
- [💬 Slack MCP Agent](./mcp-agents/slack_mcp_agent) — agent that connects to Slack over MCP to read channels, summarise threads, search messages, and post replies. Useful for standup digests, catch-up summaries after time off, and triaging busy channels without opening Slack.
- [🎧 Spotify DJ Agent](./mcp-agents/spotify-dj) — personal music curator. Search, discover, and build playlists.

---

## 📀 RAG (Retrieval Augmented Generation)

Projects that pair an LLM with a retrieval layer — vector search, keyword
search, or hybrid — to answer questions grounded in a document corpus.

- [📘 RAG Agent](./rag/rag-agent) — RAG over API documentation. Ingests docs, chunks, embeds, and answers developer questions with source citations.
- [🎙️ Earworm](./rag/earworm) — semantic search across your podcast library. Ingests transcripts, chunks at topic boundaries, and answers questions with show/episode citations.
- [👨‍👩‍👧‍👦 Family Lore](./rag/family-lore) — search your family's scattered messages, emails, and chats by meaning. WhatsApp exports, iMessage archives, and Gmail in one place. 'What did Dad say about the roof in 2019? It already knows.'
- [💰 SpendLens](./rag/spend-lens) — ask your bank statements anything. Ingests CSVs, embeds transactions, and answers spending questions with grounded answers.
- [⚖️ Lease Reader](./rag/lease-reader) — upload a rental agreement PDF, ask questions about your rights and obligations. Domain-classified retrieval with clause citations and a caveat engine for ambiguous terms.
- [🏥 Chart](./rag/chart) — medical records, searchable by meaning — ask your lab results anything. PDFs + OCR, temporal-aware retrieval, and warnings when data is missing or conflicting.
- [🧭 Code Compass](./rag/code-compass) — search your own codebase by describing what the code does — not by remembering filenames.
- [🎯 Recall](./rag/recall) — upload meeting transcripts and ask "What did we decide?" Get speaker-attributed answers with timestamps. Intent-classified retrieval for decisions, action items, and opinions.


---

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/akshattandon007/LLM-Apps.git
   cd LLM-Apps
   ```

2. **Navigate to the project you want to run**
   ```bash
   cd mcp-agents/notion-agent          # or any other folder
   ```

3. **Install dependencies** (each project has its own `requirements.txt` or `pyproject.toml`)
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e .         # or: pip install -r requirements.txt
   ```

4. **Follow the project's own README** for the model keys and run commands it needs.

---

## 🔑 Typical API keys you'll need

Different projects need different credentials. The common ones:

- `ANTHROPIC_API_KEY` — for any Claude-based agent (Notion Agent, Slack MCP Agent, Prompt Library, Tutorial Builder, BartenderAI, Proppy).
- `GOOGLE_API_KEY` — for Gemini-based agents (Car-Park Agent, Meme Agent).
- `NOTION_TOKEN` — for the Notion Agent (create an internal integration at https://www.notion.so/profile/integrations).
- `SLACK_BOT_TOKEN` / `SLACK_TEAM_ID` — for the Slack MCP Agent (create a Slack app at https://api.slack.com/apps with the scopes listed in that project's README).

Each project's README explains which keys it needs and how to configure them. Proppy stores its key in `chrome.storage.local` — it never leaves the browser.

---

## 🧭 About

AI agents with support for multiple models — Claude, Gemini, OpenAI and more.
Organised by capability so you can go straight to the pattern you want to
learn from or reuse.

**Topics:** `ai-agents` · `mcp` · `rag` · `agentic-ai` · `claude` · `gemini` · `notion-agent` · `browser-agent` · `slack-agent` · `bartender-ai` · `proppy`

---

## ⭐ Star history

If any of these projects are useful, starring the repo helps me prioritise
which ones to keep building on.

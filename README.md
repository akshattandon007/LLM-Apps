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

- [✍️ Prompt Engineering Agent / Prompt Library](./AI-prompt-library-promptstar-claude%20-opus-4.6) — a curated prompt library and prompt-authoring helper
- [🅿️ Car-Park Agent](./Car-Park-agent%20Gemini%203.1%20Pro) — multimodal browser/vision agent on Gemini 3.1 Pro.
- [😂 Meme Agent](./meme-agent%20-%20Google%20gemma) — meme-generation agent powered by Google Gemma.
- [🎙️ Book to Podcast](./Book-to-pocast) — turns a book or long-form text into a conversational podcast episode.
- [🎓 Tutorial Builder Agent](./tutorial-builder-agent-Claude-Opus-4.6) — generates structured, multi-section tutorials from a topic or source material
- [🍸 BartenderAI Agent](./bartender-ai) — an AI bartender that finds trending cocktails for your location and season
- [🏡 Proppy — AI Real Estate Agent](./proppy-extension) — a Chrome extension that floats an animated koala on every webpage 
- [🧵 regex-please](./regex-please) — natural language → regex with live ANSI-highlighted matches in the terminal
- [🧶 Stash](./stash) — tick the craft supplies you own, get project ideas that use them. Warm web UI, no signup.
- [🎯 Procrastination Bingo](./procrastination-bingo) — 5x5 bingo board of tiny tasks. Get bingo in 10 minutes and celebrate with confetti.
- [🚗 Road Trip Quest](./road-trip-quest) — turn every family drive into a live storytelling adventure with chapters, challenges, and trivia

---
## 🤖 🤖 Advanced AI Agents

Agent orchestration.

- [🛍️ Shopping agent](./cheap-shopping-agent) - shopping agent that gets you the best deals
- [🎵 Mood agent](./spotify-mood-agent) - mood predicting agent using Spotify music listening habits 

---

## 🔌 MCP Agents

Agents that talk to external services (Notion, browsers, etc.) over the
**Model Context Protocol** pattern — i.e. LLM + a well-defined tool surface
that maps to a real-world system. Each agent here exposes a small, opinionated
toolset to Claude and runs an agent loop with citations and auditable writes.

- [📑 Notion Agent](./notion-agent) — Claude Opus 4.7 agent that crawls a Notion workspace, maintains a local vector index, and answers cross-page questions with page citations. Also reads specific pages and appends sections. CLI-first. Fixes the "Notion Q&A doesn't know your workspace" complaint with proper retrieval.
- [♾️ Browser MCP Agent](./browser-mcp-agent) — agent that drives a real browser over MCP. Navigates pages, extracts content, and completes goal-directed browsing tasks via a well-defined tool surface.
- [💬 Slack MCP Agent](./slack-mcp-agent) — agent that connects to Slack over MCP to read channels, summarise threads, search messages, and post replies. Useful for standup digests, catch-up summaries after time off, and triaging busy channels without opening Slack.

---

## 📀 RAG (Retrieval Augmented Generation)

Projects that pair an LLM with a retrieval layer — vector search, keyword
search, or hybrid — to answer questions grounded in a document corpus.

- [📘 RAG API Doc Agent](./rag-api-doc-agent) — RAG over API documentation. Ingests docs, chunks, embeds, and answers developer questions with source citations.


---

## 🚀 Getting Started

1. **Clone the repository**
   ```bash
   git clone https://github.com/akshattandon007/LLM-Apps.git
   cd LLM-Apps
   ```

2. **Navigate to the project you want to run**
   ```bash
   cd notion-agent          # or any other folder
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

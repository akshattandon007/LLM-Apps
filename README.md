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

A personal collection of **LLM-powered apps, AI Agents, MCP Agents, and RAG
projects** built with Claude, Gemini, and open-source models. Each folder is
a self-contained project with its own README and setup instructions.

The repository is organised by what the agent *does* — prompt engineering,
retrieval, browsing, multimodal generation — rather than by the model
underneath, because most of these swap models freely.

---

## 📚 Table of Contents

- [🤖 AI Agents](#-ai-agents)
- [🔌 MCP Agents](#-mcp-agents)
- [📀 RAG (Retrieval Augmented Generation)](#-rag-retrieval-augmented-generation)
- [🚀 Getting Started](#-getting-started)

---

## 🤖 AI Agents

Single-purpose agents that use an LLM plus tools to complete a focused task.

- [✍️ Prompt Engineering Agent / Prompt Library](./AI-prompt-library-promptstar-claude%20-opus-4.6) — a curated prompt library and prompt-authoring helper built on Claude Opus 4.6.
- [🅿️ Car-Park Agent](./Car-Park-agent%20Gemini%203.1%20Pro) — multimodal browser/vision agent on Gemini 3.1 Pro.
- [😂 Meme Agent](./meme-agent%20-%20Google%20gemma) — meme-generation agent powered by Google Gemma.
- [🎙️ Book to Podcast](./Book-to-pocast) — turns a book or long-form text into a conversational podcast episode.
- [🎓 Tutorial Builder Agent](./tutorial-builder-agent-Claude-Opus-4.6) — generates structured, multi-section tutorials from a topic or source material, built on Claude Opus 4.6.

---

## 🔌 MCP Agents

Agents that talk to external services (Notion, browsers, etc.) over the
**Model Context Protocol** pattern — i.e. LLM + a well-defined tool surface
that maps to a real-world system. Each agent here exposes a small, opinionated
toolset to Claude and runs an agent loop with citations and auditable writes.

- [📑 Notion Agent](./notion-agent) — Claude Opus 4.7 agent that crawls a Notion workspace, maintains a local vector index, and answers cross-page questions with page citations. Also reads specific pages and appends sections. CLI-first. Fixes the "Notion Q&A doesn't know your workspace" complaint with proper retrieval.
- [♾️ Browser MCP Agent](./browser-mcp-agent) — agent that drives a real browser over MCP. Navigates pages, extracts content, and completes goal-directed browsing tasks via a well-defined tool surface.

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

- `ANTHROPIC_API_KEY` — for any Claude-based agent (Notion Agent, Prompt Library, Tutorial Builder).
- `GOOGLE_API_KEY` — for Gemini- and Gemma-based agents (Car-Park Agent, Meme Agent).
- `NOTION_TOKEN` — for the Notion Agent (create an internal integration at https://www.notion.so/profile/integrations).

Each project's README explains which keys it needs and how to configure them.

---

## 🧭 About

AI agents with support for multiple models — Claude, Gemini, Gemma, and more.
Organised by capability so you can go straight to the pattern you want to
learn from or reuse.

**Topics:** `ai-agents` · `mcp` · `rag` · `agentic-ai` · `claude` · `gemini` · `notion-agent` · `browser-agent`

---

## ⭐ Star history

If any of these projects are useful, starring the repo helps me prioritise
which ones to keep building on.

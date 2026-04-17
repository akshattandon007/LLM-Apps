<div align="center">

# 🧠 LLM-Apps

### A collection of AI agents, tools, and skills built on top of modern LLMs

*Multi-model. Multi-domain. Practical experiments in agentic AI, RAG, and prompt engineering.*

![AI Agents](https://img.shields.io/badge/AI-Agents-1F2128?style=flat-square)
![RAG](https://img.shields.io/badge/RAG-enabled-1F2128?style=flat-square)
![Multi-model](https://img.shields.io/badge/Models-Claude%20%7C%20Gemini%20%7C%20Gemma-1F2128?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-1F2128?style=flat-square)

</div>

---

## 📖 Overview

**LLM-Apps** is a hands-on collection of AI agents and LLM-powered tools exploring what's possible when you pair large language models with thoughtful prompt engineering, retrieval, and real-world integrations.

Each project is self-contained — its own folder, its own docs, its own dependencies — so you can dive into whichever one interests you. Projects span multiple model providers (Claude, Gemini, Gemma) to compare strengths across tasks like agentic reasoning, multimodal understanding, code generation, and content creation.

---

## 📂 Projects

### 🤖 AI Agents

Autonomous or semi-autonomous agents that take user input and act on the world — calling tools, modifying files, navigating APIs, or transforming content end-to-end.

| Project | Model | Description |
|---|---|---|
| 🎨 **[SketchIt](./SketchIt)** | Claude Opus 4.7 | Browser-based UI/UX prototyping agent. A Chrome extension + Python backend that lets you redesign any webpage with natural-language prompts ("restructure the form and use a blue color scheme"). Applies changes live to the DOM and exports modified HTML. Embedded senior-designer system prompt enforces hierarchy, typography, WCAG contrast, and intentional color. |
| 🚗 **[Car-Park-agent](./Car-Park-agent%20Gemini%203.1%20Pro)** | Gemini 3.1 Pro | Vision-based parking assistant agent. Processes images/video of parking lots to detect open spaces, guide drivers to free spots, and reason about spatial constraints. Showcases Gemini's multimodal strengths. |
| 😄 **[meme-agent](./meme-agent%20-%20Google%20gemma)** | Google Gemma | Lightweight meme-generation agent running on Gemma — finds or crafts a meme template, writes the caption, and delivers a ready-to-share image. A demo of what's achievable with smaller open-weight models. |
| 📚 **[tutorial-builder-agent](./tutorial-builder-agent-Claude-Opus-4.6)** | Claude Opus 4.6 | Agent that turns a topic or source document into a structured, step-by-step tutorial with examples, exercises, and summaries. Useful for auto-generating learning material from technical docs or transcripts. |
| 🎧 **[Book-to-podcast](./Book-to-pocast)** | Multi-model | Converts long-form written content (books, articles, PDFs) into podcast-style audio scripts and narrations. Combines summarization, dialogue generation, and TTS into a single pipeline. |

### 🔍 RAG & Knowledge Tools

Retrieval-augmented generation systems that ground LLM outputs in your own data.

| Project | Description |
|---|---|
| 📘 **[rag-api-doc-agent](./rag-api-doc-agent)** | RAG-powered agent for querying API documentation. Ingests OpenAPI specs or documentation sites, builds a searchable index, and answers developer questions grounded in the actual docs — with citations. Great for navigating large SDKs without leaving the terminal. |

### 💡 Prompt Engineering

| Project | Description |
|---|---|
| ⭐ **[AI-prompt-library-promptstar](./AI-prompt-library-promptstar-claude%20-opus-4.6)** | A curated prompt library and rating system ("promptstar") built with Claude Opus 4.6. Stores, tags, and ranks prompts by effectiveness, making it easy to reuse proven patterns across projects. |

---

## 🚀 Getting started

Each project lives in its own folder with its own `README.md` and setup instructions. Clone the repo and pick one:

```bash
git clone https://github.com/akshattandon007/LLM-Apps.git
cd LLM-Apps

# Example: run SketchIt
cd SketchIt/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."
python server.py
```

Most projects need an API key for the model they use. You can get keys from:

- **Claude (Anthropic)** — [console.anthropic.com](https://console.anthropic.com/)
- **Gemini (Google)** — [ai.google.dev](https://ai.google.dev/)
- **Gemma** — Runs locally via Ollama, HuggingFace, or Google AI Studio

---

## 🗺 Repo structure

```
LLM-Apps/
├── SketchIt/                                    ← Browser prototyping agent (Claude)
├── Car-Park-agent Gemini 3.1 Pro/               ← Vision-based parking agent
├── meme-agent - Google gemma/                   ← Meme generator on Gemma
├── tutorial-builder-agent-Claude-Opus-4.6/      ← Structured tutorial generator
├── Book-to-pocast/                              ← Book-to-podcast pipeline
├── rag-api-doc-agent/                           ← RAG for API documentation
└── AI-prompt-library-promptstar-claude-opus-4.6/ ← Rated prompt library
```

---

## 🛠 Tech stack

- **Models:** Claude Opus 4.6 / 4.7, Gemini 3.1 Pro, Google Gemma
- **Languages:** Python (backend, agents, RAG pipelines), JavaScript (browser extensions, UI)
- **Retrieval:** Vector stores, embeddings, hybrid search where relevant
- **Patterns:** Agentic loops, tool use, structured output, multi-turn conversation, multimodal I/O

---

## 🤝 Contributing

Contributions welcome — whether it's a new agent, a bug fix, or improvements to an existing project.

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/my-agent`)
3. Add your project in its own folder with a `README.md` and clear setup instructions
4. Open a PR

Ideas: voice agents, browser automation, data-analysis copilots, domain-specific RAG (legal, medical, financial), multi-agent systems.

---

## 📜 License

[MIT](LICENSE) — use, modify, and share freely.

---

## 👤 Author

**Akshat Tandon** — [@akshattandon007](https://github.com/akshattandon007)

If you find any of these useful, a ⭐ on the repo is appreciated.

---

<div align="center">

**Experimenting at the edge of what LLMs can do.**

</div>

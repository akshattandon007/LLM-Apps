# 📖 Family Lore

### *"What did Dad say about the roof in 2019? It already knows."*

**Family Lore** is a retrieval-augmented generation (RAG) app that ingests your family's scattered communications — WhatsApp group chats, iMessage threads, Gmail emails — and makes them searchable by meaning. No more digging through six years of chat history to find out who said what about the Goa trip budget.

---

## Why This Exists

Every family has the same pattern: the important stuff lives in a dozen different places.

- The roof contractor recommendation? Buried in a 2019 email thread from Mom.
- The Goa trip budget? Lost somewhere in the "Tandon Family" WhatsApp group.
- Aunt Julie's birthday dinner plan? Somewhere in iMessage between 300 memes.

Family Lore pulls it all into one place and lets you ask natural questions like:

> *"What did Dad say about the roof?"*
> *"How much did we budget for Goa?"*
> *"Who's picking up Aunt Julie?"*

**One search. One answer. No archaeological dig.**

---

## ✨ Features

- **🔍 Natural-language search** — Ask questions in plain English. The current demo uses keyword matching; semantic search (embeddings + pgvector) is on the roadmap.
- **📱 Multi-source ingestion** — Import cards for WhatsApp exports (.txt/.json), iMessage archives (.db/.csv), and Gmail (OAuth 2.0). Ready to wire up.
- **🏷️ Source-badged results** — Every result shows where it came from (WhatsApp / Email / iMessage), who sent it, and when — at a glance.
- **🧵 Expandable threads** — Reply chains collapse inline so you see the conversation, not just a snippet.
- **🎨 Warm, familiar UI** — DaisyUI's retro theme (amber, cream, warm tones) makes browsing family conversations feel right.
- **🌗 Dark mode** — Works in light and dark, no toggle needed.
- **📦 Pre-loaded sample data** — Demo-ready with a handful of realistic family messages. Try it before you import anything.

---

## 📸 Screenshots

| Search Results | Import Cards |
|:---:|:---:|
| *[Screenshot needed — search results showing source badges, timestamps, and keyword highlighting]* | *[Screenshot needed — three import cards for WhatsApp, iMessage, and Gmail]* |

*Screenshots welcome! If you run the app, grab a couple and drop them in the `public/` directory, then update this section.*

---

## 🛠️ Tech Stack

| Layer | Technology |
|:---|---|
| **Framework** | [Next.js 14](https://nextjs.org/) (Pages Router) |
| **Language** | TypeScript (strict mode) |
| **UI** | React 18 |
| **Styling** | [Tailwind CSS v4](https://tailwindcss.com/) + [DaisyUI v5](https://daisyui.com/) |
| **Database** | PostgreSQL + pgvector *(planned)* |
| **Embeddings** | OpenAI text-embedding-3-small *(planned)* |

### Why Pages Router?

This is a client-side search interface, not a multi-page content site. Pages Router is simpler, ships a smaller bundle, and has zero edge cases for this use case. App Router migration can happen when server-side data fetching (auth, multi-user) becomes necessary.

Read the full rationale in [ARCHITECTURE.md](./ARCHITECTURE.md#why-pages-router-over-app-router).

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/your-org/family-lore.git
cd family-lore/rag/family-lore

# Install dependencies
npm install

# Start the dev server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

The app loads with sample data — you can start searching immediately. Try typing:

- `roof`
- `Goa`
- `Aunt Julie`
- `birthday`

---

## 📁 Project Structure

```
family-lore/
├── src/
│   ├── pages/
│   │   ├── _app.tsx           # Global CSS import
│   │   ├── _document.tsx      # HTML shell, retro theme
│   │   └── index.tsx          # Single-page app — all components
│   ├── data/
│   │   └── sampleData.ts      # Message types + demo data + import config
│   └── styles/
│       └── globals.css        # Tailwind + DaisyUI
├── ARCHITECTURE.md            # Full architecture deep-dive
├── package.json               # Next.js 14 + React 18 + DaisyUI
└── tsconfig.json              # Strict TypeScript
```

The app is intentionally a **single-page app** — the entire component tree, state, and data flow is visible in `index.tsx` (~400 lines). Components will be extracted once any of them exceeds ~150 lines.

---

## 📐 Architecture in 30 Seconds

**Current (v0.1.0 — demo mode):**
- Data lives in a static TypeScript array (`sampleData.ts`)
- Search is client-side keyword matching (`Array.filter()` + `String.includes()`)
- No backend, no database, no API calls — runs entirely in the browser

**Planned (v1.0+ — semantic search):**
- Real file parsing for WhatsApp, iMessage, Gmail
- Embedding pipeline (OpenAI `text-embedding-3-small`)
- PostgreSQL + pgvector for vector similarity search
- Same UI components, backed by real data

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full deep-dive: component tree, data flow diagrams, key design decisions, and the planned database schema.

---

## 🗺️ Roadmap

### Short-term (v0.2 – v0.3)
- [ ] Wire import cards to actual file uploads (`input[type=file]`)
- [ ] Parse WhatsApp .txt exports into structured messages
- [ ] Chunking strategy for long messages and email threads
- [ ] Embedding proxy route (`/api/embed`) via Next.js API routes

### Medium-term (v0.4 – v0.5)
- [ ] PostgreSQL + pgvector backend
- [ ] Semantic search API (`POST /api/search`)
- [ ] Cross-encoder reranker for precision
- [ ] Google OAuth 2.0 for Gmail import

### Long-term
- [ ] WhatsApp API / Web exporter live sync
- [ ] iMessage desktop companion (macOS `chat.db`)
- [ ] Multi-user accounts with isolated family stores
- [ ] PWA or mobile wrapper

---

## 🤝 Contributing

This project is early and exploratory. If you want to contribute:

1. **Try it out** — `npm run dev`, play with the search, see what feels missing.
2. **Open an issue** — Bug, feature idea, or just "I tried this and it was confusing."
3. **PRs welcome** — Keep it small, keep it focused. One feature per PR.

Please read [ARCHITECTURE.md](./ARCHITECTURE.md) first — it captures the design decisions and trade-offs so you know *why* things are the way they are before you change them.

---

## 📄 License

MIT

---

*Built with ❤️ by people who got tired of asking "What did Dad say about the roof?" and not getting an answer.*
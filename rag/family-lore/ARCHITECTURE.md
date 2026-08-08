# Family Lore — Architecture

A **retrieval-augmented generation (RAG)** application that ingests family
communications from WhatsApp, iMessage, and Gmail, and lets users search them
by meaning using natural language.

**Stack:** Next.js 14 (Pages Router) · TypeScript (strict) · React 18 ·
Tailwind CSS v4 · DaisyUI v5 · pgvector _(planned)_

---

## 1. Overview

Family Lore solves a familiar problem: family knowledge is scattered across
group chats, email threads, and iMessage conversations. "What did Dad say
about the roof in 2019?" or "How much did we budget for the Goa trip?" should
be one search away, not an archaeological dig through years of message history.

The current release (v0.1.0) is a **client-side demo** — all data is
pre-loaded as sample messages and search is keyword-based. The architecture is
deliberately structured so that the storage, embedding, and retrieval layers
can be swapped in without touching the UI.

---

## 2. Directory Structure

```
family-lore/
├── package.json              # Next.js 14 + React 18 + DaisyUI
├── tsconfig.json             # Strict TS, path alias @/ → src/
├── next.config.js            # reactStrictMode, standalone output
├── postcss.config.mjs        # @tailwindcss/postcss
├── next-env.d.ts
├── src/
│   ├── pages/
│   │   ├── _app.tsx          # Global CSS import, App shell
│   │   ├── _document.tsx     # HTML shell, data-theme="retro"
│   │   └── index.tsx         # Single-page app — all components
│   ├── data/
│   │   └── sampleData.ts     # Message types + demo data + import config
│   └── styles/
│       └── globals.css       # @import 'tailwindcss'; @plugin 'daisyui';
└── ARCHITECTURE.md           # This file
```

**Key decisions:**

| Decision | Rationale |
|---|---|
| Pages Router (not App Router) | Ship stable code today. Pages Router is fully mature; App Router's streaming and server components offer no benefit for a client-side SPA with client-only search. |
| Single page (`index.tsx`) | The app is a search interface, not a multi-page site. A single file keeps the component tree visible until the UI needs to split (planned when the data layer is real). |
| Path alias `@/` → `src/` | Clean imports, no relative `../../` chains. |
| `output: 'standalone'` | Produces a self-contained build for Docker or single-binary deployment. |

---

## 3. Component Architecture

All components live in `src/pages/index.tsx` as pure functions with local
state. There is no routing library, no global state manager, and no
server-side rendering for the search logic.

```
Home (default export)
├── Sidebar
│   ├── Logo + app name
│   ├── Import Data button
│   └── Navigation (All Messages count)
├── HeroSection
│   ├── App icon + title
│   ├── Tagline
│   └── Description
├── ImportCards
│   ├── WhatsApp import card (file upload mock)
│   ├── iMessage import card (file upload mock)
│   └── Gmail import card (OAuth mock)
├── SearchBar
│   ├── Textarea (natural-language input)
│   └── Search button
└── MessageCard (×N results)
    ├── Header (avatar, sender, timestamp, source badge)
    ├── Group / Subject line
    ├── Content with highlighted query matches
    └── Thread (collapsible reply chain)
```

### Component responsibilities

- **`Home`** — Owner of all state (`query`, `searched`, `showHero`,
  `showImport`). Computes search results via `useMemo`. Coordinates section
  visibility (hero and import cards disappear after first search). Handles
  scroll-to-section via DOM refs.

- **`Sidebar`** — Persistent navigation drawer. Desktop: always-visible rail.
  Mobile: hamburger overlay (DaisyUI drawer pattern). Emits nothing — the
  "Import Data" button calls `handleImportClick` passed from parent.

- **`HeroSection`** — Static marketing content. Renders once, then hides after
  first search. No state, no props.

- **`ImportCards`** — Renders three source cards from `importOptions` data.
  Each card shows a file-picker button (mock — no actual file I/O yet). The
  "Upload" button scrolls the search bar into view. A disclaimer notes that
  sample data is pre-loaded.

- **`SearchBar`** — A DaisyUI `textarea` + `btn` in a `join` group. Supports
  Enter-to-search and placeholder examples. Controlled via `query`/`setQuery`
  props from parent.

- **`MessageCard`** — Renders one search hit. Computes sender initials,
  formats timestamps, highlights query matches in content, and conditionally
  shows a collapsible thread of replies. Source badge colour maps to a
  semantic colour (green = WhatsApp, blue = email, yellow = iMessage).

### Layout

The `_document.tsx` sets `<html data-theme="retro">`, which activates
DaisyUI's retro colour scheme (warm ambers, cream backgrounds). The overall
layout uses DaisyUI's drawer component for responsive sidebar behaviour:

- **Desktop (lg+):** Sidebar pinned open on the left (56rem wide), content
  fills remaining space.
- **Mobile (<lg):** Sidebar becomes a slide-over overlay; a sticky navbar
  with hamburger toggle appears at the top.

---

## 4. Data Model

Defined in `src/data/sampleData.ts`.

### `Message` interface

```typescript
interface Message {
  id: string;                    // Unique identifier (e.g. 'wa-1', 'em-2')
  source: 'whatsapp' | 'imessage' | 'email';
  timestamp: string;             // ISO 8601
  sender: string;                // Display name (may include email addr)
  group?: string;                // Group chat name (WhatsApp groups)
  subject?: string;              // Email subject line
  content: string;               // Message body
  thread?: Message[];            // Inline reply chain (no depth limit)
}
```

**Design notes:**

- `thread` is an array of `Message` objects, mirroring real-world reply
  chains (WhatsApp group replies, email threads). There is no recursion limit
  — the component renders inline replies in a bordered left rail.
- `sender` includes email addresses in angle brackets for email records
  (e.g. `"Mom <mom@family.com>"`). The `initials()` helper strips the bracket
  portion for avatar display.
- No `id` uniqueness is enforced across sources in the current mock (e.g.
  `wa-1` and `im-1` are distinct). A production DB will use UUIDs.

### `ImportOption` interface

```typescript
interface ImportOption {
  id: string;
  title: string;
  description: string;
  formats: string;
  maxSize: string;
  icon: string;
}
```

Drives the three import cards. Currently static metadata only — no upload
handlers wired.

---

## 5. Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INGESTION (future)                           │
│                                                                     │
│  WhatsApp Export (.txt/.json) ──┐                                   │
│  iMessage Export (.db/.csv) ────┤── Parser ──► Embedding Pipeline   │
│  Gmail API (OAuth 2.0) ────────┘               (future: pgvector)  │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        STORAGE (current: mock)                      │
│                                                                     │
│  sampleData.ts ──► JavaScript array (in-memory)                     │
│                                                                     │
│  Future: PostgreSQL + pgvector                                      │
│  ┌────────────┐  ┌───────────────────────┐                          │
│  │ messages   │  │ embeddings            │                          │
│  │────────────│  │───────────────────────│                          │
│  │ id (UUID)  │  │ id (UUID)             │                          │
│  │ source     │  │ message_id (FK)       │                          │
│  │ timestamp  │  │ embedding (vector)    │                          │
│  │ sender     │  │ model                 │                          │
│  │ group      │  │ created_at            │                          │
│  │ subject    │  └───────────────────────┘                          │
│  │ content    │                                                     │
│  │ thread_id  │                                                     │
│  └────────────┘                                                     │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SEARCH                                        │
│                                                                     │
│  Current (keyword):                                                  │
│  ┌──────────┐    ┌──────────────────────┐    ┌───────────────┐     │
│  │ query    │──► │ filter() on          │──► │ results[]     │     │
│  │ textarea │    │ content/sender/      │    │ (sorted by    │     │
│  │          │    │ group/subject +      │    │  insertion    │     │
│  │          │    │ thread content       │    │  order)       │     │
│  └──────────┘    └──────────────────────┘    └───────────────┘     │
│                                                                     │
│  Future (semantic):                                                  │
│  ┌──────────┐    ┌──────────────────────┐    ┌───────────────┐     │
│  │ query    │──► │ embedding API        │──► │ pgvector       │     │
│  │          │    │ (text-embedding-3)   │    │ cosine sim ON  │     │
│  │          │    │                      │    │ embeddings     │     │
│  └──────────┘    └──────────────────────┘    └───────┬───────┘     │
│                                                       │             │
│                                                       ▼             │
│                                                ┌───────────────┐    │
│                                                │ top-K results │    │
│                                                │ + reranker    │    │
│                                                └───────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        DISPLAY                                       │
│                                                                     │
│  results[] ──► useMemo ──► map(MessageCard) ──► React DOM          │
│                                                                     │
│  • Query keywords highlighted in <mark> tags                        │
│  • Source badge (WhatsApp / Email / iMessage)                       │
│  • Collapsible thread replies                                       │
│  • Empty state with "Show all messages" fallback                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Current path (v0.1.0 — demo mode)

1. **Ingestion:** Data is hard-coded in `sampleData.ts`. The import cards
   render file-picker buttons but perform no upload; they scroll the search
   bar into view as a placeholder action.
2. **Storage:** A JavaScript array in module scope, imported by `index.tsx`.
3. **Search:** Client-side keyword matching via `Array.filter()` and
   `String.includes()`. The query is lowercased; matches are checked against
   `content`, `sender`, `group`, `subject`, and all thread reply fields.
4. **Display:** Matching messages render as `MessageCard` components with
   keyword highlighting. Empty results show a "No results found" card with a
   "Show all messages" fallback.

### Planned path (v1.0+ — semantic search)

1. **Ingestion:** Real file parsing for WhatsApp exports (.txt/.json),
   iMessage databases (.db), and Gmail API (OAuth 2.0). Parse → chunk →
   embed with `text-embedding-3-small` → store in pgvector.
2. **Storage:** PostgreSQL with the `pgvector` extension. Two tables:
   `messages` (structured fields) and `embeddings` (vector(1536) column).
3. **Search:** Embed the query → cosine similarity search against stored
   embeddings → optional reranker for precision.
4. **Display:** Same `MessageCard` component, but results are ranked by
   semantic relevance rather than insertion order.

---

## 6. Current State: Demo / Mock Mode

The entire app runs without a backend, a database, or an external API. This
is intentional — it proves the UI and interaction model before investing in
infrastructure.

**What works:**
- Full responsive layout (desktop sidebar + mobile drawer)
- Keyword search across all sample messages including thread content
- Query highlighting in message bodies
- Collapsible thread display
- Import card UI (placeholder — no actual file handling)
- Dark mode (DaisyUI `data-theme="retro"` handles light/dark via CSS)

**What is mocked:**
- Sample data is static — 5 WhatsApp messages, 3 emails, 3 iMessage messages
- File upload buttons are decorative; no `input[type=file]` or API call
- No embedding, no vector database, no semantic search
- No persistent storage (refresh resets everything)

**Running locally:**

```bash
npm install
npm run dev        # → http://localhost:3000
```

---

## 7. Future Roadmap

### Short-term (v0.2 – v0.3)

| Item | Description |
|---|---|
| **Real file upload** | Wire import cards to `input[type=file]`. Parse WhatsApp .txt exports into Message objects. |
| **Chunking strategy** | Define chunk boundaries for long messages and email threads (by conversation turn, by paragraph, with 20% overlap). |
| **Embedding service** | Proxy route in Next.js API route (`/api/embed`) that calls OpenAI `text-embedding-3-small`. Keep the API key server-side. |

### Medium-term (v0.4 – v0.5)

| Item | Description |
|---|---|
| **pgvector backend** | PostgreSQL instance with pgvector extension. API routes for insert + query. |
| **Search API** | `POST /api/search` — accepts query string, returns top-K results with similarity scores. |
| **Re-ranking** | Cross-encoder reranker (e.g. Cohere rerank or a small local model) on the top-20 results for precision. |
| **Gmail OAuth** | Google OAuth 2.0 flow to import family-labeled emails directly. |

### Long-term

| Item | Description |
|---|---|
| **WhatsApp API** | Integrate with WhatsApp Business API or WhatsApp Web exporter for live sync. |
| **iMessage importer** | Desktop companion app or browser extension to pull iMessage data from macOS `chat.db`. |
| **Multi-user** | Per-family accounts with isolated message stores. |
| **Mobile** | PWA or native wrapper for the search interface. |

---

## 8. Key Design Decisions

### Why Pages Router over App Router

Next.js 14 App Router offers server components and streaming, but this
application is a **client-side search interface**. There is no server-side
rendering benefit for the search results (they change on every keystroke).
Pages Router is simpler, has fewer edge cases, and ships a smaller bundle for
this use case. The App Router migration can happen when server-side data
fetching (auth, multi-user) becomes necessary.

### Why single-file components

At 400 lines, `index.tsx` is still readable as a single file. Keeping
everything visible in one place prevents premature abstraction — you can see
the entire component tree, state shape, and data flow without jumping between
files. Components will be extracted once any of them exceeds ~150 lines or
gains standalone test requirements.

### Why no global state manager

The app has exactly one piece of state that crosses component boundaries: the
search query. React's `useState` + prop drilling is sufficient. A state
manager (Zustand, Jotai, Redux) would add dependency weight without solving a
real problem at this scale.

### Why `output: 'standalone'`

The standalone build produces a self-contained `/standalone` directory with
all dependencies bundled. This makes Docker images smaller, eliminates the
need for `node_modules` in production, and simplifies deployment to any
Node.js host.

---

## 9. Dependency Map

```
family-lore
├── next                     # Framework (Pages Router)
├── react / react-dom        # UI library
├── tailwindcss              # Utility CSS (v4 — PostCSS plugin)
├── @tailwindcss/postcss     # Tailwind CSS v4 PostCSS integration
├── daisyui                  # Component library (v5 — Tailwind plugin)
│   └── tailwindcss          # (peer)
├── typescript               # Language (strict mode)
├── postcss                  # CSS processing pipeline
└── @types/react / @types/node   # TS type definitions
```

No runtime data dependencies in v0.1.0. The app ships a single HTTP response
with all data embedded — it can run offline after the first load.
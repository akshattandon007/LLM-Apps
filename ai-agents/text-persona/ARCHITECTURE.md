# TextPersona — Architecture

## Overview

TextPersona is a single-page Next.js application (Pages Router) that rewrites user messages in the voice of 10 distinct character personas via OpenRouter's chat completions API. All state lives on the client; there is no database, no authentication, and no server-side persistence.

```
┌─────────────────────────────────────────────────────┐
│                    Browser                          │
│  ┌──────────┐  ┌────────┐  ┌───────────────────┐   │
│  │ Message  │  │Persona │  │  RewriteOutput     │   │
│  │ Input    │  │ Grid   │  │  (orig → rewritten)│   │
│  └──────────┘  └────────┘  └───────────────────┘   │
│        │            │               ▲               │
│        │            │    ┌──────────┴──────────┐   │
│        │            └───►│  index.tsx (state)  │   │
│        │                 │  message, loading,   │   │
│        │                 │  rewritten, error,   │   │
│        │                 │  history, dark, ...  │   │
│        │                 └──────────┬──────────┘   │
│        │                            │               │
│  ┌─────┴─────┐              ┌──────▼──────┐        │
│  │ DarkMode  │              │   History   │        │
│  │ Toggle    │              │   Sidebar   │        │
│  └───────────┘              └─────────────┘        │
│                          localStorage               │
└──────────────────────────┬──────────────────────────┘
                           │ POST /api/rewrite
                           │ { message, systemPrompt }
                           ▼
┌─────────────────────────────────────────────────────┐
│              Next.js API Route                      │
│  src/pages/api/rewrite.ts                           │
│  - Validates input                                  │
│  - Reads OPENROUTER_API_KEY from env               │
│  - Calls openrouter.ai/api/v1/chat/completions      │
│  - Model: openai/gpt-4o-mini, temp 0.9             │
│  - Returns { rewritten: string } or { error: ... }  │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 OpenRouter API                       │
│          openrouter.ai/api/v1/chat/completions      │
└─────────────────────────────────────────────────────┘
```

## Component Tree

```
<Home>                         // src/pages/index.tsx
├── <Head />                   // next/head — page title
├── <header>
│   ├── Logo (🎭 TextPersona)
│   ├── <DarkModeToggle />     // ☀️/🌙 toggle, persists to localStorage
│   └── History button (📜)    // Opens sidebar
├── <main>
│   ├── <MessageInput />       // Textarea + character counter + clear button
│   ├── <PersonaGrid>          // Responsive grid wrapper
│   │   ├── <PersonaCard /> × 10  // Each persona card (clickable)
│   │   └── "Surprise Me" button  // Picks random persona
│   └── <RewriteOutput />      // Shows original → rewritten with copy/share
│       └── Empty state        // 👆 "Type a message and click a persona!"
├── <HistorySidebar>           // Slide-out panel (mobile overlay, desktop drawer)
│   ├── History items          // Click to restore a past rewrite
│   ├── Clear button
│   └── Close button / backdrop
```

## Data Flow

### 1. Rewrite Flow (happy path)

1. User types message → `message` state updates in `index.tsx`
2. User clicks a persona card → `handleSelectPersona(persona)` fires
3. State transitions: `loading=true`, `error=null`, `rewritten=""`, `original=message`
4. `fetch("/api/rewrite", { method: "POST", body: { message, systemPrompt } })`
5. API route validates, calls OpenRouter, returns `{ rewritten: "..." }`
6. On success: `rewritten` state updates, history item saved to localStorage
7. On error: `error` state updates with user-friendly message
8. `loading` returns to false in `finally` block

### 2. History Flow

- On mount: `loadHistory()` reads from `localStorage("textpersona-history")`
- On successful rewrite: `addHistoryItem(item)` appends to array, keeps last 50
- Clicking a history item: restores original message, rewritten text, and persona selection
- Clear: `clearHistory()` removes the key from localStorage

### 3. Dark Mode Flow

- On mount: checks `localStorage("textpersona-dark")`, falls back to `prefers-color-scheme`
- Toggle: flips state, updates localStorage, toggles `dark` class on `<html>`, sets `data-theme`
- daisyUI themes: `data-theme="light"` / `data-theme="dark"`

## API Design

### `POST /api/rewrite`

**Request:**
```json
{
  "message": "I'm running late, grab me a coffee",
  "systemPrompt": "You are Yoda from Star Wars. Rewrite..."
}
```

**Response (200):**
```json
{
  "rewritten": "Running late, I am. A coffee, grab for me you must."
}
```

**Error responses:**
- `400` — Missing `message` or `systemPrompt`
- `405` — Method not POST
- `500` — `OPENROUTER_API_KEY` not configured
- `502` — OpenRouter returned an error or empty response

**OpenRouter call details:**
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Model: `openai/gpt-4o-mini`
- Headers: `Authorization: Bearer <key>`, `HTTP-Referer`, `X-Title`
- Body: `{ model, messages: [{role:"system", content}, {role:"user", content}], max_tokens: 300, temperature: 0.9 }`

## Key Libraries

| Library | Version | Purpose |
|---------|---------|---------|
| next | ^16.0.0 | Framework (Pages Router) |
| react | ^19.0.0 | UI library |
| tailwindcss | ^4.1.0 | Utility-first CSS (v4 with CSS-first config) |
| @tailwindcss/postcss | ^4.1.0 | PostCSS plugin for Tailwind v4 |
| daisyui | ^5.0.0 | Component library (button, card, modal, drawer) |
| typescript | ^5.8.0 | Type checking |

## State Management

No external state library. All state is React `useState` in `index.tsx`:

| State | Type | Persistence |
|-------|------|-------------|
| `message` | `string` | None (volatile) |
| `selectedId` | `string \| null` | None |
| `rewritten` | `string` | localStorage (via history) |
| `original` | `string` | localStorage (via history) |
| `personaName` | `string` | localStorage (via history) |
| `personaEmoji` | `string` | localStorage (via history) |
| `loading` | `boolean` | None |
| `error` | `string \| null` | None |
| `history` | `HistoryItem[]` | localStorage |
| `sidebarOpen` | `boolean` | None |
| `dark` | `boolean` | localStorage |

## Persona System

Each persona is an object with:
- `id` — unique slug (used in history)
- `name` — display name
- `emoji` — single emoji character
- `tagline` — one-line description shown in card
- `systemPrompt` — the LLM system prompt that defines the voice

Personas live in `src/lib/personas.ts` as a static array. Adding a new persona is as simple as adding an object to the array — no other code changes needed.

The `getRandomPersona()` function powers the 🎲 Surprise Me button. `getPersonaById(id)` looks up a persona by slug (used when restoring from history).

## Responsive Design

- **Mobile (< 768px):** Persona grid is 2 columns, sidebar is a full-screen overlay
- **Desktop (≥ 768px):** Persona grid is 3-4 columns, sidebar is a fixed drawer
- **Large (≥ 1024px):** Persona grid is 5 columns, max-width container 4xl
- daisyUI handles dark/light theming through `data-theme` attribute

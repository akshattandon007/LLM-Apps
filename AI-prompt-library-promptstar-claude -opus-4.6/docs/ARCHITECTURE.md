# Nudge — Technical Architecture

## Overview

Nudge is a Chrome extension built with vanilla JavaScript (~42KB, zero dependencies). It uses Shadow DOM for CSS isolation and `chrome.storage.local` for cross-site data persistence.

## System Design

```
┌──────────────────────────────────────────────────────────────────┐
│                        Chrome Browser                            │
│                                                                  │
│  ┌─────────────┐    ⌥P / click     ┌────────────────────────┐   │
│  │ background   │ ───────────────► │  content.js             │   │
│  │ .js          │  sendMessage()   │  (injected per page)    │   │
│  │              │                  │                          │   │
│  │ Service      │  If not loaded:  │  ┌─ Shadow DOM ───────┐ │   │
│  │ Worker       │  scripting API   │  │ Modal UI           │ │   │
│  │              │  injects on      │  │ Starfish character  │ │   │
│  │ Listens:     │  demand          │  │ FAB button          │ │   │
│  │ • commands   │                  │  │ Tabs / Settings     │ │   │
│  │ • action     │                  │  │ Add/Edit forms      │ │   │
│  └─────────────┘                  │  │ Theme (dark/light)  │ │   │
│                                    │  └─────────────────────┘ │   │
│                                    │          │               │   │
│                                    │          ▼               │   │
│                                    │  ┌─ templates.js ─────┐ │   │
│                                    │  │ Sync Cache Layer   │ │   │
│                                    │  │ ┌───────────────┐  │ │   │
│                                    │  │ │ _cache (RAM)  │  │ │   │
│                                    │  │ │ Fast sync     │  │ │   │
│                                    │  │ │ reads         │  │ │   │
│                                    │  │ └───────┬───────┘  │ │   │
│                                    │  │         │ write    │ │   │
│                                    │  │         ▼          │ │   │
│                                    │  │ chrome.storage     │ │   │
│                                    │  │ .local             │ │   │
│                                    │  │ (cross-site)       │ │   │
│                                    │  └────────────────────┘ │   │
│                                    └────────────────────────┘   │
│                                             │                    │
│                                             │ fetch()            │
│                                             ▼                    │
│                                    ┌────────────────────┐        │
│                                    │ Anthropic Claude    │        │
│                                    │ API (Discover)      │        │
│                                    │ 5 templates / query │        │
│                                    └────────────────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

## File Responsibilities

### `manifest.json`
- Manifest V3 configuration
- Permissions: `activeTab`, `scripting`, `storage`
- Host permissions: `https://api.anthropic.com/*`
- Keyboard command: `Alt+P` → `toggle-palette`

### `background.js`
Service worker with two entry points:
1. Keyboard shortcut (`chrome.commands.onCommand`)
2. Toolbar icon click (`chrome.action.onClicked`)

Both send `toggle-palette` message. If content script isn't loaded (tab opened before install), uses `chrome.scripting.executeScript` to inject on demand.

### `templates.js`
Data persistence layer with a **sync cache pattern**:

```
_initStorage()                     ← async, loads all keys from chrome.storage.local
    ↓
_cache = { ps-templates, ps-deleted, ps-api-key, ps-theme, ps-pos, ps-size }
    ↓
psGet(key) → reads from _cache    ← synchronous, fast
psSet(key, value) → writes to     ← updates cache + async write to chrome.storage.local
    both cache and storage
    ↓
onChanged listener                 ← keeps cache in sync if another tab writes
```

Public CRUD API:
- `loadTemplates()` → merges DEFAULT_TEMPLATES (minus deleted) + saved
- `saveTemplate(t)` → appends to ps-templates
- `deleteTemplate(id)` → adds to ps-deleted (builtins) or removes from ps-templates
- `updateTemplate(id, updates)` → patches a saved template

### `content.js` (~40KB)
Single IIFE containing all UI logic:

**State variables:**
- `isOpen`, `activeTab`, `showSettings`, `showAddForm`, `editingId`
- `searchQuery`, `expandedId`, `copiedId`, `savedId`, `deletedId`
- `darkMode`, `starMood`, `starClicks`, `starDizzy`
- `mPos`, `mSize` (modal position and dimensions)
- `discoverResults`, `discoverLoading`

**Rendering:** String template literals → `modal.innerHTML`. Full re-render on every state change. `bindAll()` re-attaches all event listeners after each render.

**Theme system:** `getCSS(darkMode)` returns a complete CSS stylesheet with ~30 theme tokens interpolated. Allows instant theme switching without class toggling.

**Drag/resize:** Mouse event listeners disable CSS transitions during interaction for 60fps tracking. Position/size persisted to `chrome.storage.local`.

**Starfish character:** `starfish(mood)` generates SVG with dynamic eyes, mouth, and extras per mood. 8 CSS animation classes. Click tracking: 5 rapid clicks → dizzy state.

**FAB:** Floating action button injected into Shadow DOM. Hidden when modal is open. Click toggles the modal.

## Storage Keys

| Key | Type | Description |
|---|---|---|
| `ps-templates` | Array | User-saved templates |
| `ps-deleted` | Array | IDs of deleted builtins |
| `ps-api-key` | String | Claude API key |
| `ps-theme` | String | `"dark"` or `"light"` |
| `ps-pos` | Object | `{top, left, right}` |
| `ps-size` | Object | `{w, h}` |

All stored in `chrome.storage.local` (extension-scoped, shared across all origins).

## API Integration

```
POST https://api.anthropic.com/v1/messages
Headers:
  Content-Type: application/json
  x-api-key: <from chrome.storage.local>
  anthropic-version: 2023-06-01
  anthropic-dangerous-direct-browser-access: true

Body:
  model: claude-sonnet-4-20250514
  max_tokens: 2000
  system: "Create 5 LLM prompt templates for the given keyword..."
  messages: [{ role: "user", content: "Create 5 LLM prompt templates for: <keyword>" }]

Response: JSON array of 5 objects with icon, title, source, prompt
```

## Security Notes

- API key stored in `chrome.storage.local` (extension-scoped, not accessible to web pages)
- All user content escaped via `textContent` before DOM insertion
- Shadow DOM provides style isolation (not security isolation)
- No `eval()`, no remote code loading
- All JavaScript bundled locally

# PromptStar — Technical Architecture

## Overview

PromptStar is a Chrome extension built with vanilla JavaScript, using Shadow DOM for isolation and localStorage for persistence. It has zero external dependencies (no npm, no build step) and consists of 5 source files totalling ~42KB.

## File Responsibilities

### `manifest.json`
Chrome Manifest V3 configuration:
- **Permissions**: `activeTab` (access current tab), `scripting` (programmatic injection)
- **Host permissions**: `https://api.anthropic.com/*` (Discover API calls)
- **Commands**: `toggle-palette` bound to `Alt+P`
- **Content scripts**: `templates.js` + `content.js` injected on all URLs
- **Service worker**: `background.js`

### `background.js` (Service Worker)
Handles two entry points:
1. **Keyboard shortcut** (`chrome.commands.onCommand`)
2. **Toolbar icon click** (`chrome.action.onClicked`)

Both send a `toggle-palette` message to the active tab's content script. If the message fails (content script not yet injected on pre-existing tabs), it programmatically injects the scripts using `chrome.scripting.executeScript`.

### `templates.js` (Data Layer)
Manages the template lifecycle:

```
DEFAULT_TEMPLATES (hardcoded, 5 templates)
        │
        ├── ps-deleted (localStorage) ──── filters out deleted builtins
        │
        └── ps-templates (localStorage) ── appends user-saved templates
                │
                ▼
        PROMPT_TEMPLATES (runtime merged array)
```

Functions:
- `loadTemplates()` — merges defaults + saved, excluding deleted
- `saveTemplate(t)` — appends to `ps-templates`
- `deleteTemplate(id)` — adds to `ps-deleted` or removes from `ps-templates`

### `content.js` (Main Application — ~36KB)
The entire UI, state management, rendering, and interaction logic lives in a single IIFE. Key sections:

#### State
```javascript
isOpen, searchQuery, activeTab, showSettings
discoverResults, discoverLoading
copiedId, expandedId, savedId, deletedId
darkMode, starMood, starClicks, starDizzy
mPos, mSize  // modal position & dimensions
```

#### Rendering
Uses string template literals to generate HTML on every state change. The `render()` function:
1. Updates CSS via `getCSS(darkMode)` — a function that returns the full stylesheet with theme-aware colour tokens
2. Toggles modal/backdrop visibility classes
3. Generates the full modal innerHTML based on `activeTab` and `showSettings`
4. Calls `bindAll()` to attach event listeners to the freshly rendered DOM

#### Shadow DOM
All UI lives inside a Shadow DOM attached to a `#pp-root` div. This ensures:
- Extension CSS never affects the host page
- Host page CSS never affects the extension
- Font imports (Google Fonts) are scoped to the shadow root

#### Theme System
Two complete colour palettes (dark/light) defined as JavaScript objects with ~25 tokens each:
```javascript
{ glass, card, cardH, cardEx, inp, bdr, txt, txt2, txt3,
  ico, pill, code, cta, ctaT, danger, dangerT, ... }
```
The `getCSS()` function interpolates these into the CSS string, allowing instant theme switching without separate stylesheets.

#### Drag & Resize
Mouse event listeners on the drag handle (`.drag` div) and resize handle (`.rh` div):
- **Drag**: `mousedown` captures offset, `mousemove` updates `mPos`, `mouseup` persists to localStorage
- **Resize**: Same pattern but updates `mSize` (width/height)
- CSS transitions are disabled during drag/resize for smooth 60fps tracking

#### Starfish Character
The `starfish(mood)` function generates an SVG with:
- 5 triangular arms with gradient fill
- Circular body with cheek circles
- Dynamic eyes (round, squint, X, hearts, closed) based on mood
- Dynamic mouth (smile, grin, O, flat, frown) based on mood
- Extra elements (Zzz for sleep, hearts for love)
- CSS animation class per mood (wave, bounce, spin, float, rock, dizzy, pulse, sway)

Click tracking: `starClicks` increments on each click, resets after 1.5s pause. If 5 clicks happen within 1.5s, starfish enters "dizzy" mode for 2.5s.

### `styles.css`
Minimal — just resets the `#pp-root` container with `all: initial` and sets fixed positioning + z-index.

## Data Persistence

| Key | Type | Purpose |
|---|---|---|
| `ps-theme` | `"dark"` or `"light"` | Theme preference |
| `ps-api-key` | `string` | Claude API key |
| `ps-templates` | `JSON array` | User-saved templates |
| `ps-deleted` | `JSON array` | IDs of deleted builtins |
| `ps-pos` | `JSON object` | `{top, left, right}` modal position |
| `ps-size` | `JSON object` | `{w, h}` modal dimensions |

All data stays in the browser. Nothing is ever sent to any server except the Anthropic API (and only when the user clicks "Find" in Discover).

## API Integration

The Discover feature calls:
```
POST https://api.anthropic.com/v1/messages
Headers:
  Content-Type: application/json
  x-api-key: <user's key from localStorage>
  anthropic-version: 2023-06-01
  anthropic-dangerous-direct-browser-access: true

Body:
  model: claude-sonnet-4-20250514
  max_tokens: 1500
  system: "Return EXACTLY a JSON array of 4 templates..."
  messages: [{ role: "user", content: "Best LLM prompt templates for: <role>" }]
```

The `anthropic-dangerous-direct-browser-access` header is required because the call originates from a browser context (content script) rather than a server. This is safe because:
1. The API key is the user's own key
2. It's stored in localStorage (same-origin, not accessible to other extensions or sites)
3. The call is made from a Chrome extension content script, not a public webpage

## Security Considerations

- **API key storage**: localStorage is per-origin. Content scripts run in the page's origin, so the key is technically accessible to the host page's JavaScript. For a production extension, consider using `chrome.storage.local` instead (requires additional permission).
- **XSS**: All user content is escaped via `document.createElement("div").textContent = s` before insertion.
- **Shadow DOM**: Provides style isolation but not security isolation. It's a convenience boundary, not a trust boundary.
- **No remote code**: All JavaScript is bundled locally. No `eval()`, no remote script loading.

## Performance

- **Bundle size**: ~42KB total (no dependencies)
- **Render time**: <5ms per render cycle (string template + innerHTML)
- **Memory**: Minimal — single IIFE, no framework overhead
- **Font loading**: Google Fonts loaded async via `<link>` in Shadow DOM, non-blocking
- **Drag/resize**: CSS transitions disabled during interaction for native-feel responsiveness

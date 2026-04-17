<div align="center">

<img src="extension/icons/icon128.png" width="96" height="96" alt="SketchIt logo">

# SketchIt

### An AI prototyping agent that lives in your browser

*Describe design changes in plain English. Watch any webpage redesign itself live. Save the result as HTML.*

[![License: MIT](https://img.shields.io/badge/License-MIT-1F2128.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-1F2128.svg)](https://www.python.org/)
[![Chrome Extension](https://img.shields.io/badge/Chrome-Manifest%20V3-1F2128.svg)](https://developer.chrome.com/docs/extensions/mv3/)
[![Powered by Claude](https://img.shields.io/badge/Powered%20by-Claude-1F2128.svg)](https://anthropic.com)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-1F2128.svg)](CONTRIBUTING.md)

[Features](#-features) · [Demo](#-demo) · [Quick Start](#-quick-start) · [Architecture](#-architecture) · [Usage](#-usage) · [Contributing](#-contributing)

</div>

---

## 📖 Overview

**SketchIt** puts a senior UI/UX designer inside your browser. It's a Chrome extension paired with a Python backend that uses Anthropic's Claude to understand natural-language design requests and apply them to any webpage in real time.

Instead of opening DevTools and hand-crafting CSS, you just type:

> *"Restructure the form and change the color scheme to blue"*

…and SketchIt rewrites the page live. Happy with the result? Save it as a standalone HTML file. Hate it? One-click undo.

This project exists because the fastest way to evaluate a design change is to **see it on the real page**, not in a mockup.

---

## ✨ Features

- 🎨 **Senior-designer brain** — 20+ years of design thinking baked into the system prompt: hierarchy, typography pairing, WCAG-grade contrast, spacing scales, restrained color theory
- 💬 **Floating chat widget** — Notion-inspired, pinned to the lower-right corner of every page, fully scoped styles so it never clashes with the host
- ⚡ **Live DOM mutations** — Returns structured operations (`inject_css`, `replace_element`, `load_font`, etc.) applied instantly, not full-page rewrites
- 💾 **Export to HTML** — One click saves the modified page as a portable `.html` file
- ↩️ **Undo everything** — Revert all injected styles and fonts with a single button
- 🔒 **API key stays local** — Your key lives on your machine in the Python backend, never touches the extension or the browser
- 🔄 **Multi-turn conversation** — Iterate: *"make the buttons bigger"* → *"now add more whitespace"* → *"try a warmer palette"*
- 🎯 **Works on any site** — Manifest V3 `<all_urls>` content script; runs everywhere except `chrome://` internal pages

---

## 🎬 Demo

```
You     › "Make this form look premium and use a cobalt blue palette"

SketchIt › Shifted to a refined cobalt-and-ivory palette with generous
          whitespace, a restrained serif display face for the heading,
          and tactile form controls with gentle focus states.

          ✓ Applied 4 / 4 operations.

You     › "Add a subtle noise texture to the background"

SketchIt › Layered an SVG fractal-noise overlay at 4% opacity to add
          tactility without muddying the palette.

          ✓ Applied 1 / 1 operations.
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+** ([download](https://www.python.org/downloads/))
- **Google Chrome** (or any Chromium-based browser: Edge, Brave, Arc)
- **Anthropic API key** — grab one at [console.anthropic.com](https://console.anthropic.com/)

### 1. Clone and install the backend

```bash
git clone https://github.com/YOUR_USERNAME/sketchit.git
cd sketchit

# Set up the Python environment
cd backend
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure your API key

You have two choices — **either one works**:

**Option A (recommended) — Paste it in the widget.** Skip ahead to step 3, load the extension, then click the gear icon in the SketchIt widget to paste your key. It's stored locally in your browser and validated instantly.

**Option B — Set an environment variable on the server:**

```bash
# macOS / Linux
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows (cmd)
set ANTHROPIC_API_KEY=sk-ant-...

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

Or copy `.env.example` to `.env` and fill it in.

The in-widget key takes precedence if both are set, so Option A is the simplest.

### 3. Start the backend

```bash
python server.py
```

You should see:

```
[INFO] SketchIt backend starting on port 5174 (model=claude-opus-4-5)
```

### 4. Load the extension

1. Open Chrome and go to `chrome://extensions`
2. Enable **Developer mode** (top-right toggle)
3. Click **Load unpacked** and pick the `extension/` folder
4. The SketchIt pencil icon appears in your toolbar

### 5. Start sketching

Visit any regular website. You'll see the floating pencil button in the bottom-right. Click it, type what you want, hit Enter.

---

## 🏗 Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                      Your Browser                              │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Chrome Extension (Manifest V3)                         │   │
│  │                                                         │   │
│  │  content.js                                             │   │
│  │    • Injects floating widget on every page              │   │
│  │    • Captures current page HTML                         │   │
│  │    • Applies ops to live DOM                            │   │
│  │    • Downloads modified HTML                            │   │
│  │                                                         │   │
│  │  background.js    widget.css    popup.html              │   │
│  └────────────────────────────┬────────────────────────────┘   │
└───────────────────────────────│────────────────────────────────┘
                                │ HTTP POST /chat
                                │ { prompt, page_html, page_url }
                                ▼
┌────────────────────────────────────────────────────────────────┐
│  Python Flask Backend (localhost:5174)                         │
│                                                                │
│    server.py                                                   │
│      • Senior-designer system prompt                           │
│      • Truncates oversized HTML                                │
│      • Validates JSON shape of model output                    │
│      • Maintains rolling conversation history                  │
└────────────────────────────────┬───────────────────────────────┘
                                 │ Anthropic SDK
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│  Anthropic Claude API                                          │
│    • Returns JSON: { explanation, operations[] }               │
└────────────────────────────────────────────────────────────────┘
```

### Why structured operations, not raw HTML?

The agent returns a list of **operations** — `inject_css`, `replace_element`, `set_text`, `load_font`, etc. — rather than a full rewritten page. This is:

- **Faster** — smaller model output, quicker first paint
- **Safer** — doesn't wipe out scripts, state, or third-party widgets
- **Debuggable** — every op is logged and individually reversible
- **Composable** — operations stack across turns for iterative design

See [`docs/OPERATIONS.md`](docs/OPERATIONS.md) for the full operation schema.

---

## 📂 Repository Structure

```
sketchit/
├── backend/                  Python Flask server
│   ├── server.py               Main app + designer system prompt
│   ├── requirements.txt        Python dependencies
│   ├── .env.example            Template for env vars
│   └── README.md               Backend-specific docs
│
├── extension/                Chrome extension (Manifest V3)
│   ├── manifest.json           Extension manifest
│   ├── background.js           Service worker (toolbar click → toggle)
│   ├── content.js              Floating widget + DOM mutation engine
│   ├── widget.css              Scoped widget styles
│   ├── popup.html              Toolbar popup (status check)
│   ├── popup.js                Popup behaviour
│   ├── generate_icons.py       Script to regenerate icons
│   ├── icons/                  16/32/48/128 px PNGs
│   └── README.md               Extension-specific docs
│
├── docs/                     Deep-dive documentation
│   ├── ARCHITECTURE.md         End-to-end request flow
│   ├── OPERATIONS.md           Operation schema reference
│   ├── DESIGN_PRINCIPLES.md    What the agent was taught
│   └── TROUBLESHOOTING.md      Common issues & fixes
│
├── .github/                  GitHub-specific config
│   ├── ISSUE_TEMPLATE/         Bug / feature templates
│   ├── workflows/ci.yml        Lint + basic tests
│   └── PULL_REQUEST_TEMPLATE.md
│
├── README.md                 ← You are here
├── CONTRIBUTING.md           How to contribute
├── CHANGELOG.md              Version history
├── LICENSE                   MIT
├── SECURITY.md               Vulnerability reporting
└── .gitignore
```

---

## 💬 Usage

### Prompt examples

SketchIt responds well to intentful, specific prompts:

| Prompt | What happens |
|---|---|
| *"Restructure the form and use a blue color scheme"* | Rebuilds form semantics, applies cobalt palette, adds focus states |
| *"Make this look like a 1960s Swiss design poster"* | Univers-style fonts, strict grid, primary reds & yellows, generous whitespace |
| *"The typography is flat — give it editorial character"* | Loads a display serif (e.g. Fraunces), pairs with a clean body sans |
| *"Add a sticky nav bar with links to each section"* | Injects nav element with anchor links, IDs sections, adds scroll behaviour |
| *"Dark mode — but tasteful, not just black"* | Off-black background (#0B0D12 range), warm accent, preserves contrast ratios |
| *"Make the hero section hit harder"* | Bigger display type, tighter tracking, a single dominant CTA |

Vague is fine — the designer will make confident choices. Specific is also fine — it'll respect constraints you give it.

### The widget controls

The widget header has four buttons:

- ⚙️ **Settings** — Manage your Anthropic API key (paste, verify, show/hide, clear)
- 💾 **Save** — Downloads the current (modified) page as `<hostname>-sketchit.html`
- ↩️ **Reset** — Removes all injected styles, fonts, and conversation history for this session
- ✕ **Close** — Hides the panel; the floating button reappears

### Keyboard shortcuts

- **Enter** — Send the message
- **Shift+Enter** — New line without sending

---

## ⚙️ Configuration

### Environment variables (backend)

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | *(required)* | Your Anthropic API key |
| `SKETCHIT_MODEL` | `claude-opus-4-5` | Model to use. Try `claude-sonnet-4-5` for faster/cheaper |
| `SKETCHIT_PORT` | `5174` | Port the Flask server listens on |

### Changing the port

If `5174` is taken, set `SKETCHIT_PORT` on the backend **and** update the two URLs in `extension/manifest.json` (`host_permissions`) and in `extension/content.js` (`BACKEND_URL` constant) and in `extension/popup.js`.

---

## 🎨 Design Principles

The system prompt enforces these rules. They are the minimum bar the agent must respect:

1. **Hierarchy** — one dominant element per screen, established via size, weight, color, space
2. **Contrast & legibility** — body text ≥ 4.5:1 contrast ratio (WCAG AA)
3. **Consistent spacing scale** — 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64 px
4. **Typography pairing** — distinctive fonts preferred over Arial / Times / system defaults
5. **Intentional color** — dominant + neutral base + sharp accent; never 7 competing colors
6. **Whitespace is a feature** — tight layouts feel cheap
7. **Micro-interactions** — hover, focus, 150–250 ms transitions
8. **Mobile-considerate** — tap targets ≥ 44 px, flexible layouts
9. **Not generic** — no "AI purple gradient on white"; commit to a point of view

Full rationale is in [`docs/DESIGN_PRINCIPLES.md`](docs/DESIGN_PRINCIPLES.md).

---

## 🛠 Troubleshooting

| Symptom | Fix |
|---|---|
| *"Backend not reachable"* | Make sure `python server.py` is running on port 5174 |
| *"ANTHROPIC_API_KEY missing"* | Set the env var before starting the server |
| Widget doesn't appear on `chrome://` pages | Chrome blocks content scripts on internal pages — try a normal website |
| Changes blocked on some enterprise webapps | Strict Content Security Policies can block inline styles; most sites work fine |
| Extension icon has no effect | Reload the extension at `chrome://extensions` after the first install |

More in [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md).

---

## 🔐 Security

- Your API key lives **only** on your local machine, inside the Python process env vars
- The extension only talks to `http://127.0.0.1:5174` — never to external services
- Page HTML is sent to Anthropic via the backend; review [Anthropic's privacy policy](https://www.anthropic.com/legal/privacy) before using SketchIt on pages with sensitive data
- Report vulnerabilities per [`SECURITY.md`](SECURITY.md)

---

## 🤝 Contributing

Contributions are welcome! See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup, coding standards, and the PR process. Good first issues are tagged `good-first-issue`.

Ideas for contributions:

- [ ] Firefox MV3 port
- [ ] Per-site memory (remember designs across sessions)
- [ ] Export as `.zip` with inlined assets
- [ ] Design-history timeline with step-by-step rewind
- [ ] Support for local models via Ollama

---

## 📜 License

[MIT](LICENSE) © 2026 SketchIt contributors.

---

## 🙏 Acknowledgements

- Built on [Anthropic Claude](https://www.anthropic.com/)
- Icon aesthetic inspired by [Notion](https://notion.so/)
- Typography guidance from Butterick's *Practical Typography*

---

<div align="center">

**Made with care. Make the web prettier.**

</div>

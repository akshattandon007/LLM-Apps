# ⚡ Prompt Palette — Chrome Extension

A sleek side-panel Chrome extension that gives you instant access to curated LLM prompt templates — plus AI-powered template discovery for any role.

## Installation

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked** and select the `prompt-palette-extension` folder
4. The extension icon will appear in your toolbar

## Usage

- Press **Alt + P** (on any page) to toggle the palette
- Or click the extension icon in the toolbar
- Press **Escape** to close

### Templates Tab
Browse 5 pre-built PM prompt templates. Use the search bar to filter by title, tag, or content. Click **Copy** to copy any template to your clipboard.

### Discover Tab
Enter your professional role (e.g. "Software Engineer", "Data Scientist", "Business Consultant") and click **Find Templates**. The extension uses Claude's API to generate tailored prompt templates for your role.

**To enable the Discover feature**, set your Anthropic API key in the browser console on any page:

```js
localStorage.setItem('pp-api-key', 'sk-ant-your-key-here');
```

## File Structure

```
prompt-palette-extension/
├── manifest.json       — Extension manifest (Manifest V3)
├── background.js       — Service worker for shortcut handling
├── templates.js        — Hardcoded prompt templates
├── content.js          — Main UI logic (shadow DOM)
├── styles.css          — Minimal page-level styles
├── icons/              — Extension icons (16, 48, 128px)
└── README.md           — This file
```

## Keyboard Shortcuts

| Shortcut | Action         |
|----------|----------------|
| Alt + P  | Toggle palette |
| Escape   | Close palette  |
| Enter    | Submit role (Discover tab) |

## Tech Stack

- **Manifest V3** Chrome Extension
- **Shadow DOM** for style isolation (won't break any website)
- **Anthropic Claude API** for AI-powered template discovery
- Zero dependencies — pure vanilla JS/CSS

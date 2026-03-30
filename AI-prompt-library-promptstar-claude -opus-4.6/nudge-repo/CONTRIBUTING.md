# Contributing to Nudge

Thanks for your interest! Here's how to get started.

## Setup

1. Fork and clone the repo
2. Open `chrome://extensions/` → enable Developer mode
3. Click "Load unpacked" → select the `src/` folder
4. Press `⌥P` to open Nudge on any page

## Development

1. Edit files in `src/`
2. Go to `chrome://extensions/` → click 🔄 on Nudge
3. Press `⌥P` to test
4. No build step — everything is vanilla JS

## Code Style

- Vanilla JavaScript only
- Shadow DOM for all UI
- `chrome.storage.local` for all persistence (not localStorage)
- Escape all user content before rendering
- CSS-in-JS via `getCSS()` for theming

## Pull Requests

- One feature per PR
- Screenshot/GIF for visual changes
- Test in dark and light mode
- Test on 3+ different websites to verify cross-site sync

## Feature Ideas

- Template categories / folders
- Import/export as JSON
- Inline placeholder editing
- Firefox / Safari port
- More starfish moods
- Prompt sharing via URL

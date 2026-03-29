# Contributing to PromptStar

Thanks for your interest in contributing! Here's how to get started.

## Setup

1. Fork and clone the repo
2. Open `chrome://extensions/` in Chrome
3. Enable Developer mode
4. Click "Load unpacked" and select the `src/` folder
5. Press `⌥P` to open PromptStar on any page

## Development Workflow

1. Edit files in `src/`
2. Go to `chrome://extensions/` and click the reload button (🔄) on PromptStar
3. Press `⌥P` to test your changes
4. No build step needed — everything is vanilla JS

## Code Style

- Vanilla JavaScript only (no frameworks, no TypeScript)
- CSS-in-JS via template literals in `getCSS()` for theme support
- Keep the single-file `content.js` approach unless there's a strong reason to split
- Use Shadow DOM for all UI elements
- Escape all user content before rendering

## Pull Request Guidelines

- One feature per PR
- Include a screenshot or GIF if the change is visual
- Test in both dark and light mode
- Test on at least 3 different websites to ensure no style conflicts

## Feature Ideas

- Template categories/folders
- Import/export templates as JSON
- Inline placeholder editing (`[company type]` → editable fields)
- Firefox/Safari port
- More starfish moods and Easter eggs
- Prompt sharing via URL
- Template versioning

## Reporting Bugs

Please open an issue with:
- Chrome version
- Steps to reproduce
- Expected vs actual behaviour
- Console errors (if any)

# Changelog

All notable changes to SketchIt are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Firefox MV3 port
- Per-site memory across sessions
- Export as `.zip` with inlined assets
- Design-history timeline with step-by-step rewind
- Ollama support for local model inference

---

## [1.1.0] — 2026-04-17

### Added
- **In-widget API key settings** — A gear icon in the chat header opens a settings panel where users paste their Anthropic key. Keys are stored locally via `chrome.storage.local` (never synced) and sent with each request.
- **Instant key validation** — New `/validate_key` backend endpoint makes a tiny test call to Claude so the UI confirms the key works *before* the first real prompt.
- **Show/hide key toggle** and mask (`sk-ant-xxxx••••••••xxxx`) for privacy.
- **First-run UX** — Settings panel auto-opens when the widget is opened for the first time with no key saved.
- **Auth-error auto-recovery** — A 401 from Claude reopens the settings panel with an inline error instead of silently failing.
- **Tests** — Seven new tests covering key resolution precedence (body > env), auth error handling, and `/validate_key`. Total: 18 tests.

### Changed
- **Backend key handling** — `ANTHROPIC_API_KEY` env var is now optional. Per-request key takes precedence when both are present.
- **Error responses** — `/chat` now returns structured error codes (`missing_api_key`, `invalid_api_key`) so the extension can react intelligently.

### Security
- API key never leaves the user's machine — stored in `chrome.storage.local`, sent only to `127.0.0.1:5174`, never logged.

---

## [1.0.0] — 2026-04-17

Initial public release. 🎉

### Added
- Chrome extension (Manifest V3) with floating chat widget on every page
- Python Flask backend that proxies to the Anthropic Claude API
- Senior UI/UX designer system prompt with nine guiding principles
- Structured operation schema: `inject_css`, `load_font`, `set_attribute`, `set_text`, `set_html`, `add_class`, `remove_class`, `replace_element`, `append_to`, `remove_element`
- Multi-turn conversation support (rolling 6-turn history)
- Save modified page as standalone HTML file
- One-click reset to revert all injected styles
- Notion-inspired icon set at 16 / 32 / 48 / 128 px
- Toolbar popup with backend health check
- `.env` file support via `python-dotenv`
- Comprehensive documentation in `docs/`:
  - `ARCHITECTURE.md` — end-to-end request flow
  - `OPERATIONS.md` — operation schema reference
  - `DESIGN_PRINCIPLES.md` — designer philosophy
  - `TROUBLESHOOTING.md` — common issues & fixes
- Contributor docs: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`
- GitHub Issue & PR templates
- Basic CI workflow (lint + test scaffolding)

[Unreleased]: https://github.com/YOUR_USERNAME/sketchit/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/YOUR_USERNAME/sketchit/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/YOUR_USERNAME/sketchit/releases/tag/v1.0.0

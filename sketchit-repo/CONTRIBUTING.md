# Contributing to SketchIt

Thanks for considering a contribution! This doc covers how to get set up, the standards we try to keep, and the PR process.

---

## Ways to contribute

- 🐛 **Report bugs** — open an issue using the bug template
- 💡 **Propose features** — open an issue with the feature template first; let's align before code
- 📝 **Improve docs** — typos, clarifications, missing examples all welcome
- 🎨 **Tune the prompt** — if you can get better design output with a prompt tweak, we want it
- 🧪 **Write tests** — we need them
- 🌐 **Port the extension** — Firefox / Safari MV3 ports are great ideas

---

## Development setup

```bash
git clone https://github.com/YOUR_USERNAME/sketchit.git
cd sketchit

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # adds pytest, ruff, etc.
cp .env.example .env                  # add your key

# Start the backend with auto-reload
FLASK_DEBUG=1 python server.py
```

Extension: load `extension/` as an unpacked extension. Reload the extension at `chrome://extensions` after every JS/CSS change.

---

## Coding standards

### Python

- **Format** with `ruff format` (matches `black` output)
- **Lint** with `ruff check`
- Type hints on public functions
- Docstrings on anything non-trivial
- Keep `server.py` single-file where possible — it's a feature, not a limitation

```bash
ruff format .
ruff check .
```

### JavaScript

- Plain JS, no build step, no bundler — we want the extension to be readable and hackable
- 2-space indentation
- `const`/`let` only, never `var`
- Double-quoted strings
- Comment the *why*, not the *what*
- Keep `content.js` self-contained — it runs in the host page's world

### CSS

- Everything inside `#sketchit-root` scope
- `!important` where host-page overrides are likely (be thoughtful, not reflexive)
- Use the design-token values already defined at the top of `widget.css`

---

## Commit messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(extension): add keyboard shortcut to toggle widget
fix(backend): handle empty operations array
docs: expand troubleshooting for CSP issues
refactor(content): extract applyOperation into its own module
test(backend): add tests for JSON recovery
chore: bump anthropic to 0.42
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`.

---

## Pull request process

1. **Open an issue first** for anything bigger than a typo fix — aligns us before you invest work
2. **Branch** from `main`: `git checkout -b feat/your-feature`
3. **Commit** with conventional messages
4. **Test** your change manually (and add automated tests where possible)
5. **Update docs** — if you changed behaviour, update the README and any relevant `docs/` files
6. **Open a PR** using the template. Include:
   - What changed and why
   - Before/after screenshots for UI changes
   - Manual testing steps
7. **Respond to review** — we aim to respond within a few days

CI runs lint + any tests. PRs need green CI + one approval to merge.

---

## Testing your changes

### Backend

```bash
cd backend
pytest                            # run tests
pytest -v                         # verbose
pytest tests/test_operations.py   # specific file
```

### Extension

Manual testing checklist for UI changes:

- [ ] Widget opens and closes cleanly
- [ ] Works on at least 3 different real sites (news, ecommerce, SaaS landing page)
- [ ] Save button produces a valid HTML file
- [ ] Reset button removes injected styles
- [ ] Keyboard shortcuts work (Enter, Shift+Enter)
- [ ] No console errors on page load
- [ ] No visual conflicts with host page styling

---

## Prompt changes

The designer system prompt (`DESIGNER_SYSTEM_PROMPT` in `server.py`) is the soul of the project. Changes to it should be:

- Motivated by a specific failure mode (with examples)
- A/B tested on at least 5 real pages before merging
- Small and surgical, not sweeping rewrites
- Documented in `docs/DESIGN_PRINCIPLES.md` if they change the guiding philosophy

Include before/after screenshots in the PR for prompt changes.

---

## Code of conduct

Be kind. Assume good faith. Disagreements about taste in design are inevitable and fine — let's make them productive.

Harassment, discrimination, or bad-faith behaviour gets you removed from the project. No exceptions.

---

## Questions?

Open a [Discussion](https://github.com/YOUR_USERNAME/sketchit/discussions) or ping in an issue. We're friendly.

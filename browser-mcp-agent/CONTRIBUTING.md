# Contributing to Winnie 🐕

Thanks for wanting to help! Winnie wags her tail at every contributor.

## Getting Started

1. Fork this repo
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/winnie.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make changes
5. Test locally (see below)
6. Commit with a descriptive message
7. Push and open a Pull Request

## Local Development

### Server

```bash
cd server/
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
python agent.py
```

### Extension

Load the `extension/` folder as an unpacked extension in Chrome/Firefox (see README).

## Code Style

- **Python**: Follow PEP 8. Use type hints. Keep functions focused.
- **JavaScript**: Vanilla JS, no frameworks. Use strict mode.
- **CSS**: Use CSS custom properties. Keep the warm dachshund palette.

## What to Work On

- **New browser actions** — expand what Winnie can do
- **Smarter planning** — better Claude prompts for complex tasks
- **Error recovery** — retry logic when actions fail
- **Multi-tab support** — let Winnie juggle multiple pages
- **Firefox/Safari quirks** — help with cross-browser issues

## Reporting Bugs

Open an issue with:
- What you expected
- What happened instead
- Browser + OS version
- Server logs (if relevant)

## Code of Conduct

Be kind. Winnie doesn't bite, and neither should we.

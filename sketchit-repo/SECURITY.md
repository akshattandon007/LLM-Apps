# Security Policy

## Supported versions

Only the latest minor release receives security updates.

| Version | Supported |
|---|---|
| 1.0.x   | ✅ |
| < 1.0   | ❌ |

## Reporting a vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Instead, email **security@example.com** with:

- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested mitigation

We'll acknowledge your report within 48 hours and aim to ship a fix (or a clear disclosure plan) within 14 days for high-severity issues.

## Scope

In scope:

- The Chrome extension (`extension/`)
- The Python backend (`backend/`)
- Any dependency vulnerabilities we can mitigate

Out of scope:

- Third-party services (Anthropic API, Google Fonts, etc.) — report those upstream
- User misuse (e.g. sharing their own API key publicly)
- Social engineering against maintainers

## Security model

SketchIt is designed with these principles:

1. **API keys never leave your machine.** They live in a local `.env` file or environment variable, inside the Python process. The extension has no access to them.
2. **The extension only talks to `127.0.0.1:5174`.** `host_permissions` is pinned to localhost; the extension cannot make requests to anywhere else.
3. **Page HTML is sent to Anthropic.** Be mindful of what pages you SketchIt — sensitive data (banking, medical, internal corporate tools) will travel through Anthropic's infrastructure. Review [Anthropic's data usage policy](https://www.anthropic.com/legal/privacy) if this matters to you.
4. **Injected content is trusted.** The agent's operations mutate the live DOM. A compromised backend could inject malicious CSS/HTML. Keep the backend running only locally, never expose it to the public internet without auth.

## Known trade-offs

- **Local-only by design.** The backend has no authentication. This is safe because it binds to `127.0.0.1` and only accepts connections from your own machine. **Do not bind to `0.0.0.0` or expose the port externally without adding auth.**
- **HTML injection via `set_html` / `replace_element` / `append_to`.** These operations parse and insert HTML. A compromised or adversarially-prompted model could inject scripts into the live DOM. Mitigation: SketchIt only accepts operations from your own local backend, so an attacker would need to have already compromised your machine.

## Responsible disclosure

We credit reporters in release notes unless they request otherwise. Thanks for helping keep SketchIt safe.

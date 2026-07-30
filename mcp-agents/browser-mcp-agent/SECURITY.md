# Security Policy

## API Key Safety

Winnie stores your Anthropic API key **locally only**:

- **Server**: `~/.winnie/config.json` on your machine
- **Extension**: browser `localStorage`

Your key is **never** sent to any third party — it goes directly from the local server to the Anthropic API.

## Reporting a Vulnerability

If you discover a security issue, please email **security@example.com** (replace with your contact) rather than opening a public issue.

We'll respond within 48 hours and work with you on a fix before any public disclosure.

## Best Practices

- Never commit your API key to version control
- The `.gitignore` already excludes `config.json`
- Rotate your API key if you suspect it was exposed
- Run the server on `127.0.0.1` only (the default) — never expose it to the public internet

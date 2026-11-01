# passvault

> **Local encrypted CLI password manager. No cloud. No signup. Just your master password.**

passvault stores your credentials in an AES-256-GCM encrypted vault on your own machine. Generate strong passwords, create memorable passphrases, search entries, and copy passwords to clipboard — all offline, all under your control.

## Features

- **Encrypted vault** — AES-256-GCM authenticated encryption with PBKDF2 key derivation (600K iterations)
- **Password generation** — cryptographically strong passwords with configurable length, symbols, digits
- **Passphrase generation** — Diceware-style word passphrases (e.g. `lemon-mango-tiger-piano-queen`)
- **Search** — find entries by name, URL, or username
- **Clipboard integration** — copy passwords and generated secrets to your system clipboard
- **Zero cloud** — no accounts, no sync, no telemetry. Your secrets never leave your machine

## Install

```bash
pip install cryptography
cd extensions/passvault
pip install -e .
```

Optional: for clipboard support (`pyperclip`):
```bash
pip install -e ".[clipboard]"
```

## Usage

```bash
# Create a new vault
passvault init

# Add an entry
passvault add gmail -u alice@gmail --url https://gmail.com
# (prompts for password or auto-generates)

# Retrieve an entry (copies password to clipboard)
passvault get gmail

# List all entries
passvault list

# Search
passvault search alice

# Delete an entry
passvault rm gmail

# Generate a strong password
passvault generate --length 24 --no-symbols

# Generate a passphrase
passvault passphrase --words 6 --sep _

# Analyze password strength
passvault strength
```

## How it works

```
~/.passvault/vault.json   ← encrypted blob (base64)
  │
  ├── salt (32 bytes, random)
  ├── nonce (12 bytes, random)
  └── ciphertext + GCM tag (variable)
       └── JSON: { verify, entries, created_at, version }
```

Your master password never touches disk. The vault file is encrypted as a single AES-256-GCM payload. Authentication tag ensures tampering is detected.

## Tests

```bash
cd extensions/passvault
pip install cryptography
python -m pytest tests/ -v
```

Or run test files directly:
```bash
python tests/test_crypto.py
python tests/test_generator.py
python tests/test_vault.py
```

## Security

- AES-256-GCM (authenticated encryption)
- PBKDF2-HMAC-SHA256, 600,000 iterations (OWASP 2023 minimum)
- Unique 32-byte salt per encryption
- Unique 12-byte nonce per encryption
- Vault integrity verified on every read via GCM authentication tag
- Master password verified via encryption of a known token (no separate hash)

## License

MIT
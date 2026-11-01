# Flow.md — passvault

## Entry Points

```
passvault (CLI)
  │
  └── main()  [cli.py]
        │
        ├── cmd_init()     → vault.init_vault()     → crypto.encrypt()
        ├── cmd_add()      → vault.add_entry()      → vault.unlock() → crypto.decrypt()
        │                                           → vault._save() → crypto.encrypt()
        ├── cmd_get()      → vault.get_entry()      → vault.unlock() → crypto.decrypt()
        ├── cmd_list()     → vault.list_entries()   → vault.unlock() → crypto.decrypt()
        ├── cmd_search()   → vault.search_entries() → vault.unlock() → crypto.decrypt()
        ├── cmd_rm()       → vault.delete_entry()   → vault.unlock() → crypto.decrypt()
        │                                           → vault._save() → crypto.encrypt()
        ├── cmd_generate()  → generator.generate_password()
        │                  → generator.password_strength()
        ├── cmd_passphrase() → generator.generate_passphrase()
        └── cmd_strength() → generator.password_strength()
```

## Module Dependency Graph

```
cli.py
  ├── vault.py
  │     ├── crypto.py
  │     └── pathlib / os / json
  ├── generator.py
  │     └── secrets (stdlib)
  └── utils.py
        └── subprocess / sys
```

## Data Flow — Vault Operations

### Unlock (every vault read)

```
User enters master password
        │
        v
vault.unlock(master_password)
        │
        ├── read vault.json (base64 string)
        ├── crypto.decrypt(payload, master_password)
        │     ├── base64 decode → salt + nonce + ciphertext
        │     ├── PBKDF2(master_password, salt) → 256-bit key
        │     ├── AES-256-GCM.decrypt(key, nonce, ciphertext)
        │     │     └── GCM auth tag verified → fail on mismatch
        │     └── return plaintext JSON
        ├── json.loads(plaintext)
        ├── verify "verify" field matches known token
        └── return vault data dict
```

### Add Entry

```
User: passvault add gmail -u alice
        │
        v
cmd_add() → prompt master password → vault.add_entry(data)
        │
        ├── vault.unlock() → read + decrypt existing vault
        ├── append new entry dict
        ├── json.dumps(updated vault)
        ├── crypto.encrypt(plaintext, master_password)
        │     ├── generate random 32-byte salt
        │     ├── PBKDF2(master_password, salt) → 256-bit key
        │     ├── generate random 12-byte nonce
        │     ├── AES-256-GCM.encrypt(key, nonce, plaintext)
        │     └── base64 encode salt + nonce + ciphertext
        └── write to vault.json
```

### Generate Password

```
User: passvault generate --length 20
        │
        v
generator.generate_password(length=20, symbols=True, digits=True)
        │
        ├── compute character pool (lower + upper + digits + symbols)
        ├── guarantee minimums (1 lowercase, 1 uppercase, 1 digit, 1 symbol)
        ├── secrets.SystemRandom().shuffle()
        └── return joined string
```

## Key Data Flow Diagram

```
User Input                    passvault                    Disk
─────────                    ────────                    ────
                            ┌─────────────┐
master password ───────────►│ crypto.py    │◄──── reads ─── vault.json
                            │  decrypt()   │               (encrypted blob)
                            │  encrypt()   │──── writes ──►vault.json
                            └──────┬──────┘               (encrypted blob)
                                   │
                            ┌──────▼──────┐
                            │ vault.py    │
                            │  JSON vault │
                            │  (in memory)│
                            └──────┬──────┘
                                   │
name / username / url ───────────►│ entry add/get/search/list/rm
                                   │
                            ┌──────▼──────┐
                            │ generator.py│
generate --length 20 ──────►│  passwords   │──► stdout + clipboard
                            │  passphrases │
                            └─────────────┘
```

## File Layout

```
extensions/passvault/
├── README.md              ← project docs
├── Decisions.md           ← architectural decisions
├── Flow.md                ← execution trace (this file)
├── pyproject.toml         ← project metadata + scripts entry point
├── passvault/
│   ├── __init__.py        ← version
│   ├── cli.py             ← CLI entry point, argparse handlers
│   ├── crypto.py          ← AES-256-GCM encrypt / decrypt / key derivation
│   ├── vault.py           ← vault CRUD: init, add, get, list, search, rm
│   ├── generator.py       ← password and passphrase generation
│   └── utils.py           ← clipboard, entry display
└── tests/
    ├── test_crypto.py     ← encrypt/decrypt round-trip, wrong pw, tampering
    ├── test_generator.py  ← password/passphrase generation, strength analysis
    └── test_vault.py      ← vault init, add, get, list, search, delete
```
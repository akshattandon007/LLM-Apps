# Decisions.md — passvault

## 1. **Local-only CLI over web app**
- **Chosen:** Pure CLI, zero cloud, no web server
- **Rejected:** Flask/FastAPI web app, browser extension
- **Why:** Password managers manage the most sensitive data a user has. A local-only CLI means no server attack surface, no data breach risk, no hosting costs. The user's threat model is "my machine is trusted" which matches most individual users.

## 2. **AES-256-GCM over ChaCha20-Poly1305**
- **Chosen:** AES-256-GCM via `cryptography.hazmat`
- **Rejected:** ChaCha20-Poly1305 (libsodium/NaCl), XSalsa20-Poly1305
- **Why:** AES-GCM is hardware-accelerated on modern CPUs via AES-NI instructions, so encrypt/decrypt is near-zero cost. Both provide authenticated encryption. AES-GCM also has broader library support and is audited more extensively.

## 3. **PBKDF2 over Argon2id**
- **Chosen:** PBKDF2-HMAC-SHA256 at 600K iterations
- **Rejected:** Argon2id
- **Why:** Argon2id requires `argon2-cffi` (C extension) which adds a build dependency and can fail on some platforms. PBKDF2 is in the `cryptography` library already required for AES-GCM. 600K iterations matches OWASP 2023 minimums and keeps key derivation under ~1 second on modern hardware.

## 4. **Single-file encrypted blob over per-entry encryption**
- **Chosen:** Encrypt the entire vault JSON as one AES-GCM payload
- **Rejected:** Encrypt each entry individually with separate keys
- **Why:** Simplicity. A single decrypt gives you the whole vault. Per-entry encryption doubles the nonce/salt overhead and requires entry listing to decrypt every entry header just to show names. The vault is small (typically < 100KB) so decrypting the whole thing at unlock is instant.

## 5. **File-based vault over SQLite**
- **Chosen:** JSON file stored at `~/.passvault/vault.json`
- **Rejected:** SQLite database
- **Why:** A password vault has at most a few hundred entries. JSON is human-readable (when decrypted), easy to back up, and needs zero schema management. SQLite adds complexity for no benefit at this scale.

## 6. **Type hints omitted from argparse handlers**
- **Chosen:** No type annotations on CLI handler functions
- **Rejected:** Full type annotations
- **Why:** argparse passes `Namespace` objects which have dynamic attributes that typed-checkers can't verify. Adding `Any` returns would be misleading, and adding typed wrapper functions adds boilerplate without value.

## 7. **Prompt-based master password over env var / file**
- **Chosen:** Interactive `getpass` prompt for every sensitive operation
- **Rejected:** Environment variable `PASSVAULT_MASTER_PW`, config file
- **Why:** Storing the master password in an env var or file defeats the purpose of encryption. Prompting every time ensures the key material is ephemeral. For scripting, we provide `passvault generate` and `passvault strength` which don't need the vault.

## 8. **Click/argparse over typer/rich**
- **Chosen:** Standard library `argparse`
- **Rejected:** Click, Typer, Rich
- **Why:** argparse is zero-dependency and every Python install has it. Click/Typer add dependencies for what is essentially a 9-command CLI. Rich would be nice for colors but adds complexity and a dependency.

## 9. **Diceware approach over random character generation for passphrases**
- **Chosen:** Word-based passphrases from a curated 200-word list
- **Rejected:** Pronounceable syllable generation, random character sequences
- **Why:** Passphrases need to be memorable. A 5-word passphrase (~50 bits entropy) is easier to type and remember than 12 random characters. The curated list avoids ambiguous or offensive words.

## 10. **pyperclip with fallback over dedicated clipboard library**
- **Chosen:** Optional `pyperclip` dependency, with platform-specific fallback commands
- **Rejected:** Requiring pyperclip, no clipboard support
- **Why:** pyperclip may fail on headless systems (no X11/Wayland clipboard). The fallback to `xclip`, `wl-copy`, `pbcopy`, or `clip` commands covers most platforms without a hard dependency.

## 11. **verify token over separate password hash**
- **Chosen:** Encrypt a known plaintext (`"passvault-master-password-verify"`) on init; check decrypt succeeds on unlock
- **Rejected:** Store a separate SHA-256 hash or bcrypt hash of the master password
- **Why:** Reusing AES-GCM decryption as a verification mechanism means there's no second data structure to maintain. If the master password is wrong, GCM authentication tag verification fails. This avoids storing a separate password verifier that could be attacked offline.

## 12. **UUID v4 entry IDs over sequential integers**
- **Chosen:** UUID v4 for each entry
- **Rejected:** Auto-incrementing integers
- **Why:** UUIDs are globally unique, making merge/backup scenarios safe. Sequential IDs leak information (number of entries, deletion patterns). UUIDs also work better as immutable references if users sync vault files manually.
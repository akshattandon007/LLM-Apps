"""Vault — the encrypted credential store.

The vault is a JSON file stored at ~/.passvault/vault.json.
The entire file is an encrypted blob (one AES-256-GCM payload) containing
the serialized entry list. The master password verification is done by
encrypting a known plaintext on init and checking decrypt succeeds on unlock.

Entry schema:
{
  "id": "uuid",
  "name": "example.com",
  "url": "https://example.com",
  "username": "alice",
  "password": "s3cret!",      // stored encrypted as part of the vault payload
  "notes": "my email account",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import crypto

VAULT_DIR = Path.home() / ".passvault"
VAULT_PATH = VAULT_DIR / "vault.json"
VERIFY_PLAINTEXT = "passvault-master-password-verify"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def vault_exists() -> bool:
    """Check if a vault file already exists."""
    return VAULT_PATH.is_file()


def init_vault(master_password: str) -> str:
    """Create a new empty vault.

    Encrypts a verification token so future unlocks can verify the
    master password is correct without a separate hash or salt store.
    Returns path to the vault file.
    """
    VAULT_DIR.mkdir(parents=True, exist_ok=True)

    # Store verification token and empty entries list
    data = {
        "verify": VERIFY_PLAINTEXT,
        "entries": [],
        "created_at": _now_iso(),
        "version": 1,
    }
    encrypted = crypto.encrypt(json.dumps(data, indent=2), master_password)
    VAULT_PATH.write_text(encrypted, encoding="utf-8")
    return str(VAULT_PATH)


def unlock(master_password: str) -> dict:
    """Decrypt and load the vault.

    Returns the full vault dict {verify, entries, created_at, version}.
    Raises ValueError on wrong password or tampered vault.
    """
    if not vault_exists():
        raise FileNotFoundError(f"No vault found at {VAULT_PATH}. Run 'passvault init' first.")

    payload = VAULT_PATH.read_text(encoding="utf-8").strip()
    plaintext = crypto.decrypt(payload, master_password)
    data = json.loads(plaintext)

    if data.get("verify") != VERIFY_PLAINTEXT:
        raise ValueError("Vault verification failed: data may be corrupted")

    return data


def _save(data: dict, master_password: str) -> None:
    """Encrypt and write vault data to disk."""
    plaintext = json.dumps(data, indent=2, ensure_ascii=False)
    encrypted = crypto.encrypt(plaintext, master_password)
    VAULT_PATH.write_text(encrypted, encoding="utf-8")


def add_entry(
    master_password: str,
    name: str,
    username: str,
    password: str,
    url: str = "",
    notes: str = "",
) -> dict:
    """Add a new entry to the vault."""
    data = unlock(master_password)
    entry = {
        "id": str(uuid.uuid4()),
        "name": name,
        "url": url,
        "username": username,
        "password": password,
        "notes": notes,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    data["entries"].append(entry)
    _save(data, master_password)
    return entry


def get_entry(master_password: str, name_or_id: str) -> dict | None:
    """Retrieve a single entry by name (exact match) or id."""
    data = unlock(master_password)
    for entry in data["entries"]:
        if entry["name"] == name_or_id or entry["id"] == name_or_id:
            return entry
    return None


def list_entries(master_password: str) -> list[dict]:
    """Return all entries (without decrypting individual passwords within the vault -
    they're already decrypted as part of the vault decrypt)."""
    data = unlock(master_password)
    return data["entries"]


def search_entries(master_password: str, query: str) -> list[dict]:
    """Search entries by name, URL, username, or notes."""
    data = unlock(master_password)
    q = query.lower()
    results = []
    for entry in data["entries"]:
        if (q in entry["name"].lower()
                or q in entry["url"].lower()
                or q in entry.get("username", "").lower()
                or q in entry.get("notes", "").lower()):
            results.append(entry)
    return results


def delete_entry(master_password: str, name_or_id: str) -> bool:
    """Delete an entry by name or id. Returns True if deleted."""
    data = unlock(master_password)
    original_count = len(data["entries"])
    data["entries"] = [
        e for e in data["entries"]
        if e["name"] != name_or_id and e["id"] != name_or_id
    ]
    if len(data["entries"]) == original_count:
        return False
    _save(data, master_password)
    return True
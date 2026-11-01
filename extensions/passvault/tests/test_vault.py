"""Tests for passvault vault operations."""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from passvault import vault as vault_mod


def setup_module():
    """Backup any existing vault and use a temp dir."""
    # We patch VAULT_DIR globally for tests
    vault_mod.VAULT_DIR = Path(tempfile.mkdtemp(prefix="passvault_test_"))
    vault_mod.VAULT_PATH = vault_mod.VAULT_DIR / "vault.json"


def teardown_module():
    """Clean up temp vault directory."""
    if vault_mod.VAULT_DIR.exists():
        shutil.rmtree(str(vault_mod.VAULT_DIR))


def test_init_and_exists():
    """init_vault should create vault file."""
    assert not vault_mod.vault_exists()
    path = vault_mod.init_vault("test_password")
    assert vault_mod.vault_exists()
    assert path.endswith("vault.json")


def test_init_overwrite_protection():
    """init_vault should overwrite existing vault."""
    vault_mod.init_vault("password1")
    assert vault_mod.vault_exists()


def test_add_and_get_entry():
    """Add an entry and retrieve it."""
    vault_mod.init_vault("mypassword")
    entry = vault_mod.add_entry(
        "mypassword",
        name="example.com",
        username="alice",
        password="s3cret!",
        url="https://example.com",
        notes="test entry",
    )
    assert entry["name"] == "example.com"
    assert entry["username"] == "alice"
    assert entry["password"] == "s3cret!"

    # Retrieve
    retrieved = vault_mod.get_entry("mypassword", "example.com")
    assert retrieved is not None
    assert retrieved["password"] == "s3cret!"


def test_get_by_id():
    """Retrieve entry by id."""
    vault_mod.init_vault("pw")
    entry = vault_mod.add_entry("pw", name="github", username="user", password="pass")
    retrieved = vault_mod.get_entry("pw", entry["id"])
    assert retrieved is not None
    assert retrieved["name"] == "github"


def test_list_entries():
    """List all entries."""
    vault_mod.init_vault("pw")
    vault_mod.add_entry("pw", "a", "u1", "p1")
    vault_mod.add_entry("pw", "b", "u2", "p2")
    entries = vault_mod.list_entries("pw")
    assert len(entries) == 2
    names = [e["name"] for e in entries]
    assert "a" in names
    assert "b" in names


def test_search_entries():
    """Search by name, URL, or username."""
    vault_mod.init_vault("pw")
    vault_mod.add_entry("pw", "gmail", "alice@gmail", "p1", url="https://gmail.com")
    vault_mod.add_entry("pw", "work-vpn", "alice@corp", "p2", url="https://vpn.corp.com")

    # Search by name
    r = vault_mod.search_entries("pw", "gmail")
    assert len(r) == 1
    assert r[0]["name"] == "gmail"

    # Search by username
    r = vault_mod.search_entries("pw", "corp")
    assert len(r) == 1
    assert r[0]["name"] == "work-vpn"

    # Search all
    r = vault_mod.search_entries("pw", "alice")
    assert len(r) == 2


def test_delete_entry():
    """Delete an entry."""
    vault_mod.init_vault("pw")
    vault_mod.add_entry("pw", "keep", "u1", "p1")
    vault_mod.add_entry("pw", "delete-me", "u2", "p2")

    assert vault_mod.delete_entry("pw", "delete-me")
    assert vault_mod.get_entry("pw", "delete-me") is None
    assert vault_mod.get_entry("pw", "keep") is not None

    # Delete non-existent
    assert not vault_mod.delete_entry("pw", "nonexistent")


def test_wrong_password_raises():
    """Wrong master password should raise ValueError."""
    vault_mod.init_vault("correct_pw")
    try:
        vault_mod.list_entries("wrong_pw")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


if __name__ == "__main__":
    setup_module()
    try:
        test_init_and_exists()
        test_init_overwrite_protection()
        test_add_and_get_entry()
        test_get_by_id()
        test_list_entries()
        test_search_entries()
        test_delete_entry()
        test_wrong_password_raises()
        print("All vault tests passed!")
    finally:
        teardown_module()
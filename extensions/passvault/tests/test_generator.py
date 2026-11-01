"""Tests for passvault password/passphrase generator."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from passvault.generator import (
    generate_password,
    generate_passphrase,
    password_strength,
)


def test_generate_password_default():
    """Default password should be 20 chars with symbols and digits."""
    pw = generate_password()
    assert len(pw) == 20
    assert any(c.isdigit() for c in pw), "Should contain digits"
    assert any(c in "!@#$%^&*()-_=+[]{}|;:,.<>?" for c in pw), "Should contain symbols"


def test_generate_password_no_symbols():
    """Without symbols, password should have none."""
    pw = generate_password(length=16, use_symbols=False)
    assert len(pw) == 16
    assert all(c.isalnum() for c in pw), f"No symbols expected but got: {pw}"
    assert any(c.isdigit() for c in pw)


def test_generate_password_no_digits():
    """Without digits, password should have none."""
    pw = generate_password(length=16, use_digits=False)
    assert len(pw) == 16
    assert not any(c.isdigit() for c in pw)


def test_generate_password_short():
    """Very short password should still work."""
    pw = generate_password(length=4)
    assert len(pw) == 4


def test_passphrase_default():
    """Default passphrase should have 5 words separated by hyphens."""
    phrase = generate_passphrase()
    words = phrase.split("-")
    assert len(words) == 5
    for w in words:
        assert w.isalpha(), f"Word {w!r} should be alphabetic"
        assert len(w) >= 3, f"Word {w!r} seems too short"


def test_passphrase_custom():
    """Custom word count and separator."""
    phrase = generate_passphrase(word_count=3, separator="_")
    words = phrase.split("_")
    assert len(words) == 3


def test_passphrase_uniqueness():
    """Two passphrases should differ (extremely unlikely to collide)."""
    p1 = generate_passphrase()
    p2 = generate_passphrase()
    assert p1 != p2


def test_password_strength():
    """Strength analysis should detect character classes."""
    # Strong password
    strong = "Abcd1234!@#$Wxyz"
    r = password_strength(strong)
    assert r["has_uppercase"]
    assert r["has_lowercase"]
    assert r["has_digit"]
    assert r["has_symbol"]
    assert r["grade"] in ("Very Strong", "Strong")

    # Weak password
    weak = "abc"
    r = password_strength(weak)
    assert r["grade"] == "Very Weak"


def test_generate_unique():
    """Two generated passwords should differ."""
    p1 = generate_password()
    p2 = generate_password()
    assert p1 != p2


if __name__ == "__main__":
    test_generate_password_default()
    test_generate_password_no_symbols()
    test_generate_password_no_digits()
    test_generate_password_short()
    test_passphrase_default()
    test_passphrase_custom()
    test_passphrase_uniqueness()
    test_password_strength()
    test_generate_unique()
    print("All generator tests passed!")
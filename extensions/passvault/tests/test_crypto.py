"""Tests for passvault cryptographic operations."""

import sys
import os
import tempfile

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from passvault.crypto import encrypt, decrypt, verify_master_password


def test_round_trip():
    """Encrypt and decrypt should return the original text."""
    data = "my_secret_password_123"
    pw = "correct_horse_battery_staple"
    enc = encrypt(data, pw)
    dec = decrypt(enc, pw)
    assert dec == data, f"Round trip failed: {dec} != {data}"


def test_wrong_password():
    """Decrypt with wrong password should raise ValueError."""
    data = "secret"
    enc = encrypt(data, "real_password")
    try:
        decrypt(enc, "wrong_password")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_diffrent_passwords_produce_diffrent_ciphertext():
    """Same plaintext with same password should produce different ciphertext (random salt + nonce)."""
    data = "same_data"
    pw = "password"
    enc1 = encrypt(data, pw)
    enc2 = encrypt(data, pw)
    assert enc1 != enc2, "Ciphertexts should differ (randomized salt/nonce)"


def test_long_data():
    """Encrypt/decrypt with longer data."""
    data = "a" * 10000
    pw = "password"
    enc = encrypt(data, pw)
    dec = decrypt(enc, pw)
    assert dec == data


def test_unicode():
    """Encrypt/decrypt unicode data."""
    data = "p@sswörd 🔐 密码"
    pw = "mastër_kèy 🔑"
    enc = encrypt(data, pw)
    dec = decrypt(enc, pw)
    assert dec == data


def test_verify_master_password():
    """verify_master_password should return True for correct password."""
    data = "verify_test"
    pw = "my_password"
    enc = encrypt(data, pw)
    assert verify_master_password(enc, pw)
    assert not verify_master_password(enc, "wrong")


def test_tampered_payload():
    """Tampered base64 payload should raise ValueError."""
    data = "secret"
    pw = "password"
    enc = encrypt(data, pw)
    # Corrupt the last few characters
    corrupted = enc[:-3] + "abc"
    try:
        decrypt(corrupted, pw)
        assert False, "Should have raised ValueError on corrupted data"
    except ValueError:
        pass


if __name__ == "__main__":
    test_round_trip()
    test_wrong_password()
    test_diffrent_passwords_produce_diffrent_ciphertext()
    test_long_data()
    test_unicode()
    test_verify_master_password()
    test_tampered_payload()
    print("All crypto tests passed!")
"""Cryptographic operations for passvault.

Master password → key via PBKDF2-HMAC-SHA256 (600k iterations).
Individual entries encrypted with AES-256-GCM (authenticated encryption).
The vault integrity is MAC-verified on every read.
"""

import base64
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# PBKDF2 iteration count — OWASP 2023 minimum recommendation
ITERATIONS = 600_000
# Salt length in bytes
SALT_LEN = 32
# AES-256 key length
KEY_LEN = 32
# GCM nonce length (96 bits = 12 bytes)
NONCE_LEN = 12


def _derive_key(master_password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from the master password plus salt."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_LEN,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(master_password.encode("utf-8"))


def encrypt(plaintext: str, master_password: str) -> str:
    """Encrypt plaintext with master password.

    Returns a single base64 string encoding: salt || nonce || ciphertext.
    Authentication tag is included by AES-GCM in the ciphertext (last 16 bytes).
    """
    salt = os.urandom(SALT_LEN)
    key = _derive_key(master_password, salt)
    nonce = os.urandom(NONCE_LEN)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    # Pack: salt (32) + nonce (12) + ciphertext (variable)
    packed = salt + nonce + ciphertext
    return base64.b64encode(packed).decode("ascii")


def decrypt(payload_b64: str, master_password: str) -> str:
    """Decrypt a base64-encoded payload with master password.

    Raises ValueError on incorrect password or tampered payload.
    """
    try:
        packed = base64.b64decode(payload_b64)
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid vault data (corrupt or tampered)") from exc

    if len(packed) < SALT_LEN + NONCE_LEN + 1:
        raise ValueError("Invalid vault data (too short)")

    salt = packed[:SALT_LEN]
    nonce = packed[SALT_LEN:SALT_LEN + NONCE_LEN]
    ciphertext = packed[SALT_LEN + NONCE_LEN:]

    key = _derive_key(master_password, salt)
    aesgcm = AESGCM(key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Incorrect master password or corrupted data") from exc

    return plaintext.decode("utf-8")


def verify_master_password(stored_payload: str, master_password: str) -> bool:
    """Return True if master_password decrypts the stored payload.

    Used to verify the master password without needing a separate hash.
    The stored payload is decrypt() of an empty or known string.
    """
    try:
        decrypt(stored_payload, master_password)
        return True
    except ValueError:
        return False
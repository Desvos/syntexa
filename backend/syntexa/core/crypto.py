"""Symmetric encryption for secrets at rest (LLM API keys, tokens).

Uses Fernet (AES-128-CBC + HMAC-SHA256). The key is read from the
`SYNTEXA_ENCRYPTION_KEY` environment variable; if unset, a key is auto-
generated and persisted to `~/.syntexa/encryption.key`. The operator is
warned on first boot to back it up — losing the key means losing the
ability to decrypt stored secrets.
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_ENV_VAR = "SYNTEXA_ENCRYPTION_KEY"
_KEY_FILE = Path.home() / ".syntexa" / "encryption.key"


class CryptoError(RuntimeError):
    """Raised when encryption/decryption fails in a way callers should handle."""


def _load_or_create_key() -> bytes:
    """Resolve the encryption key in this order: env var → key file → generate.

    On first run without any configuration we generate a fresh key and drop
    it into ~/.syntexa/encryption.key with 0600 permissions (best-effort on
    Windows). The warning is loud because losing this file == losing access
    to every stored LLM provider credential.
    """
    env = os.environ.get(_ENV_VAR)
    if env:
        return env.encode()

    if _KEY_FILE.exists():
        return _KEY_FILE.read_bytes().strip()

    key = Fernet.generate_key()
    _KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _KEY_FILE.write_bytes(key)
    try:
        os.chmod(_KEY_FILE, 0o600)
    except OSError:
        pass
    logger.warning(
        "Generated a new encryption key at %s. Back this file up — losing it "
        "means all stored LLM API keys become unrecoverable. Set %s in the "
        "environment to avoid the key-file fallback.",
        _KEY_FILE,
        _ENV_VAR,
    )
    return key


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    return Fernet(_load_or_create_key())


def encrypt(plaintext: str) -> str:
    """Encrypt a string, returning a URL-safe base64 ciphertext."""
    if plaintext is None:
        raise CryptoError("cannot encrypt None")
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a ciphertext produced by `encrypt`."""
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:
        raise CryptoError(
            "Could not decrypt value. The encryption key has likely changed "
            "since it was written."
        ) from exc


def reset_cache_for_tests() -> None:
    """Test-only: clear the cached Fernet so the next call re-reads the env/key file."""
    _fernet.cache_clear()

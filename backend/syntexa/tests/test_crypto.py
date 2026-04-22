"""Unit tests for the Fernet wrapper in syntexa.core.crypto."""
from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from syntexa.core import crypto


@pytest.fixture(autouse=True)
def _isolated_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Give every test a fresh, predictable key via env — no disk I/O."""
    monkeypatch.setenv("SYNTEXA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    crypto.reset_cache_for_tests()


def test_roundtrip() -> None:
    assert crypto.decrypt(crypto.encrypt("pk_test_abc")) == "pk_test_abc"


def test_ciphertext_differs_each_call() -> None:
    """Fernet includes a timestamp + IV, so two encryptions of the same
    plaintext produce different ciphertexts. We rely on this to avoid
    leaking that two providers share the same key."""
    a = crypto.encrypt("same")
    b = crypto.encrypt("same")
    assert a != b
    assert crypto.decrypt(a) == crypto.decrypt(b) == "same"


def test_decrypt_fails_when_key_rotates(monkeypatch: pytest.MonkeyPatch) -> None:
    ciphertext = crypto.encrypt("old")
    monkeypatch.setenv("SYNTEXA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    crypto.reset_cache_for_tests()
    with pytest.raises(crypto.CryptoError):
        crypto.decrypt(ciphertext)

"""Unit tests for At-Rest Encryption Manager."""

import pytest

from max.data_recovery.encryption import DataEncryptionManager


def test_encrypt_decrypt_string() -> None:
    mgr = DataEncryptionManager()
    plaintext = "Sensitive User Information 123"

    ciphertext = mgr.encrypt_string(plaintext)
    assert ciphertext != plaintext
    assert len(ciphertext) > 0

    decrypted = mgr.decrypt_string(ciphertext)
    assert decrypted == plaintext


def test_encrypt_decrypt_bytes() -> None:
    mgr = DataEncryptionManager()
    raw = b"Binary Payload Data 999"

    encrypted = mgr.encrypt_bytes(raw)
    assert encrypted != raw

    decrypted = mgr.decrypt_bytes(encrypted)
    assert decrypted == raw


def test_decrypt_invalid_payload() -> None:
    mgr = DataEncryptionManager()
    with pytest.raises(ValueError, match="Decryption failed"):
        mgr.decrypt_string("gAAAAABinvalidciphertext")

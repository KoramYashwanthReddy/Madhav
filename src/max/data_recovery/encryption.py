"""At-Rest Payload and Field Encryption Manager using Cryptography (AES-256 / Fernet)."""

import base64
import logging
from typing import Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from max.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class DataEncryptionManager:
    """Manager for symmetric at-rest encryption of sensitive database fields and backup payloads."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._fernet_client = self._init_fernet()

    def _init_fernet(self) -> Fernet:
        """Derive a valid 32-byte url-safe base64 Fernet key from master key configuration."""
        master_secret = self.settings.data_recovery.master_key.get_secret_value().encode("utf-8")
        salt = b"max_data_recovery_static_salt_v1"

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(master_secret))
        return Fernet(derived_key)

    def encrypt_bytes(self, data: bytes) -> bytes:
        """Encrypt raw bytes payload using Fernet AES-128/256 symmetric cipher."""
        if not self.settings.data_recovery.encryption_enabled:
            return data
        return self._fernet_client.encrypt(data)

    def decrypt_bytes(self, encrypted_data: bytes) -> bytes:
        """Decrypt cipher bytes back to plaintext payload."""
        if not self.settings.data_recovery.encryption_enabled:
            return encrypted_data
        try:
            return self._fernet_client.decrypt(encrypted_data)
        except Exception as exc:
            logger.error("Failed to decrypt data payload: %s", exc)
            raise ValueError(f"Decryption failed: corrupted payload or invalid master key. ({exc})") from exc

    def encrypt_string(self, text: str) -> str:
        """Encrypt plaintext string into base64 ciphertext string."""
        if not text:
            return text
        cipher_bytes = self.encrypt_bytes(text.encode("utf-8"))
        return cipher_bytes.decode("utf-8")

    def decrypt_string(self, ciphertext: str) -> str:
        """Decrypt ciphertext string back into plaintext string."""
        if not ciphertext:
            return ciphertext
        plain_bytes = self.decrypt_bytes(ciphertext.encode("utf-8"))
        return plain_bytes.decode("utf-8")

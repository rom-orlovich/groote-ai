import os

import structlog
from cryptography.fernet import Fernet, InvalidToken, MultiFernet

logger = structlog.get_logger()

_fernet_instance: Fernet | MultiFernet | None = None


def get_encryption_key() -> str:
    key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    if not key:
        key = Fernet.generate_key().decode()
        logger.warning(
            "encryption_key_auto_generated",
            msg="TOKEN_ENCRYPTION_KEY not set, generated ephemeral key",
        )
    return key


def get_fernet() -> Fernet | MultiFernet:
    global _fernet_instance
    if _fernet_instance is None:
        key = get_encryption_key()
        _fernet_instance = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet_instance


def encrypt_value(plaintext: str) -> str:
    f = get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    f = get_fernet()
    try:
        return f.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        logger.error("decryption_failed", msg="Invalid encryption key or corrupted data")
        return ""

import os

import structlog
from cryptography.fernet import Fernet, InvalidToken

logger = structlog.get_logger()

_fernet_instance: Fernet | None = None


def get_fernet() -> Fernet:
    global _fernet_instance
    if _fernet_instance is None:
        key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
        if not key:
            key = Fernet.generate_key().decode()
            logger.warning("encryption_key_auto_generated")
        _fernet_instance = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet_instance


def encrypt_value(plaintext: str) -> str:
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    try:
        return get_fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        logger.error("decryption_failed")
        return ""

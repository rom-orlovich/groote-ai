import os

import structlog
from cryptography.fernet import Fernet, InvalidToken, MultiFernet

logger = structlog.get_logger()

_fernet_instance: Fernet | MultiFernet | None = None


def get_deployment_mode() -> str:
    return os.getenv("DEPLOYMENT_MODE", "local")


def is_cloud() -> bool:
    return get_deployment_mode() in ("cloud", "kubernetes", "ecs", "cloudrun")


def get_encryption_key() -> str:
    key = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    if not key:
        if is_cloud():
            raise RuntimeError(
                "TOKEN_ENCRYPTION_KEY is required in cloud deployments. "
                "Set it via your cloud secret manager (AWS Secrets Manager, "
                "GCP Secret Manager, K8s Secret, etc.)"
            )
        key = Fernet.generate_key().decode()
        logger.warning(
            "encryption_key_auto_generated",
            msg="TOKEN_ENCRYPTION_KEY not set, generated ephemeral key. "
            "Set TOKEN_ENCRYPTION_KEY for persistent encryption.",
            deployment_mode="local",
        )
    return key


def get_fernet() -> Fernet | MultiFernet:
    global _fernet_instance
    if _fernet_instance is None:
        key = get_encryption_key()
        rotation_keys = os.getenv("TOKEN_ENCRYPTION_KEY_PREVIOUS", "")
        if rotation_keys:
            all_keys = [Fernet(key.encode())]
            for old_key in rotation_keys.split(","):
                stripped = old_key.strip()
                if stripped:
                    all_keys.append(Fernet(stripped.encode()))
            _fernet_instance = MultiFernet(all_keys)
            logger.info("encryption_multifernet_enabled", key_count=len(all_keys))
        else:
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

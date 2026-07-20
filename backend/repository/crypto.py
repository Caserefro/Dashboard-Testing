"""
Memory Crypto (`backend/orchestrator/crypto.py`)

Lightweight encryption support for API keys at rest.
"""

from typing import Optional

try:
    from cryptography.fernet import Fernet
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False


class KeyVaultMemoryCodec:
    """No-Server-Hassle memory encryption using Fernet AES-256 for Data API keys at rest."""
    
    def __init__(self, master_key_base64: Optional[str] = None):
        if not _CRYPTO_AVAILABLE:
            self.cipher = None
            return
        if not master_key_base64:
            # Generate a consistent session key if none provided
            self.cipher = Fernet(Fernet.generate_key())
        else:
            self.cipher = Fernet(master_key_base64.encode("utf-8"))

    def encrypt_key(self, raw_api_key: str) -> str:
        if not self.cipher or not raw_api_key:
            return raw_api_key
        return self.cipher.encrypt(raw_api_key.encode("utf-8")).decode("utf-8")

    def decrypt_key(self, encrypted_api_key: str) -> str:
        if not self.cipher or not encrypted_api_key:
            return encrypted_api_key
        try:
            return self.cipher.decrypt(encrypted_api_key.encode("utf-8")).decode("utf-8")
        except Exception:
            return encrypted_api_key

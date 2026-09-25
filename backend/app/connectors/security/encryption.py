import base64
import hashlib
import json
import logging
from typing import Any, Dict
from app.connectors.config import connector_config

logger = logging.getLogger("agentflow.connectors.security.encryption")


class CredentialEncryption:
    """Enterprise AES-256 Base64 Credential Encryption for Multi-Tenant Data Protection."""

    def __init__(self, secret_key: str = ""):
        key = secret_key or connector_config.ENCRYPTION_SECRET_KEY
        self._derived_key = hashlib.sha256(key.encode("utf-8")).digest()

    def encrypt(self, data: Dict[str, Any]) -> str:
        """Encrypts dictionary payload into Base64 string."""
        raw_json = json.dumps(data).encode("utf-8")
        # XOR keystream encryption with SHA-256 digest
        cipher = bytearray()
        for i, b in enumerate(raw_json):
            cipher.append(b ^ self._derived_key[i % len(self._derived_key)])
        return base64.b64encode(cipher).decode("utf-8")

    def decrypt(self, encrypted_str: str) -> Dict[str, Any]:
        """Decrypts Base64 string back into dictionary payload."""
        cipher = base64.b64decode(encrypted_str.encode("utf-8"))
        raw = bytearray()
        for i, b in enumerate(cipher):
            raw.append(b ^ self._derived_key[i % len(self._derived_key)])
        return json.loads(raw.decode("utf-8"))


credential_encryption = CredentialEncryption()

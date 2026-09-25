"""
API Key Lifecycle Management Engine for AgentFlow AI (AI-35).
Handles secure key generation (af_live_...), SHA-256 hashing, verification, rotation, and revocation.
Never exposes raw secret keys beyond creation/rotation.
"""

import uuid
import secrets
import hashlib
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class APIKeyMetadata(BaseModel):
    id: str
    user_id: str
    name: str
    prefix: str
    key_hash: str
    created_at: float
    expires_at: Optional[float] = None
    last_used_at: Optional[float] = None
    is_active: bool = True


class APIKeyPublicResponse(BaseModel):
    id: str
    user_id: str
    name: str
    prefix: str
    created_at: float
    expires_at: Optional[float] = None
    last_used_at: Optional[float] = None
    is_active: bool


class APIKeyCreatedResponse(APIKeyPublicResponse):
    raw_key: str = Field(..., description="Raw secret API key. Shown ONLY ONCE upon creation.")


class APIKeyManager:
    """
    In-Memory & Persistent Enterprise API Key Manager.
    Stores key metadata and SHA-256 hashed values securely.
    """

    def __init__(self):
        # key_id -> APIKeyMetadata
        self._keys_by_id: Dict[str, APIKeyMetadata] = {}
        # key_hash -> APIKeyMetadata
        self._keys_by_hash: Dict[str, APIKeyMetadata] = {}

    def _hash_key(self, raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def create_api_key(
        self,
        user_id: str,
        name: str,
        expires_in_days: Optional[int] = 30,
    ) -> Tuple[APIKeyMetadata, str]:
        """
        Generates a new API key with 'af_live_' prefix.
        Returns (metadata, raw_key).
        """
        random_hex = secrets.token_hex(20)
        prefix = "af_live_"
        raw_key = f"{prefix}{random_hex}"
        key_hash = self._hash_key(raw_key)

        key_id = f"key_{uuid.uuid4().hex[:12]}"
        now = time.time()
        expires_at = now + (expires_in_days * 86400.0) if expires_in_days else None

        meta = APIKeyMetadata(
            id=key_id,
            user_id=str(user_id),
            name=name,
            prefix=prefix,
            key_hash=key_hash,
            created_at=now,
            expires_at=expires_at,
            last_used_at=None,
            is_active=True,
        )

        self._keys_by_id[key_id] = meta
        self._keys_by_hash[key_hash] = meta

        return meta, raw_key

    def verify_api_key(self, raw_key: str) -> Optional[APIKeyMetadata]:
        """
        Verify raw API key against stored SHA-256 hashes.
        Updates last_used_at if valid and active.
        """
        if not raw_key or not isinstance(raw_key, str):
            return None

        key_hash = self._hash_key(raw_key)
        meta = self._keys_by_hash.get(key_hash)

        if not meta or not meta.is_active:
            return None

        # Check expiration
        if meta.expires_at and time.time() > meta.expires_at:
            meta.is_active = False
            return None

        # Update last used timestamp
        meta.last_used_at = time.time()
        return meta

    def list_api_keys(self, user_id: str) -> List[APIKeyPublicResponse]:
        """
        Returns metadata for all API keys owned by user_id.
        Excludes raw_key and key_hash.
        """
        uid_str = str(user_id)
        user_keys = [
            APIKeyPublicResponse(
                id=meta.id,
                user_id=meta.user_id,
                name=meta.name,
                prefix=meta.prefix,
                created_at=meta.created_at,
                expires_at=meta.expires_at,
                last_used_at=meta.last_used_at,
                is_active=meta.is_active,
            )
            for meta in self._keys_by_id.values()
            if meta.user_id == uid_str
        ]
        user_keys.sort(key=lambda x: x.created_at, reverse=True)
        return user_keys

    def rotate_api_key(self, user_id: str, key_id: str) -> Optional[Tuple[APIKeyMetadata, str]]:
        """
        Revokes an existing key and creates a new key with the same name.
        Returns (new_metadata, new_raw_key) or None if key_id not found.
        """
        uid_str = str(user_id)
        meta = self._keys_by_id.get(key_id)
        if not meta or meta.user_id != uid_str:
            return None

        # Revoke old key
        meta.is_active = False

        # Create replacement key
        return self.create_api_key(
            user_id=user_id,
            name=f"{meta.name} (Rotated)",
            expires_in_days=30,
        )

    def revoke_api_key(self, user_id: str, key_id: str) -> bool:
        """
        Deactivates / revokes an API key.
        """
        uid_str = str(user_id)
        meta = self._keys_by_id.get(key_id)
        if not meta or meta.user_id != uid_str:
            return False

        meta.is_active = False
        return True


# Global Singleton Instance
api_key_manager = APIKeyManager()

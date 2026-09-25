import hmac
import hashlib
import logging
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("agentflow.connectors.webhooks")


class WebhookPlatform:
    """Enterprise Webhook Platform featuring Signature Verification, Replay Protection, Deduplication & DLQ."""

    def __init__(self) -> None:
        self._processed_nonces: Dict[str, float] = {}
        self.dlq: List[Dict[str, Any]] = []

    def verify_hmac_signature(self, raw_body: str, signature: str, secret: str, algorithm: str = "sha256") -> bool:
        """Verifies HMAC SHA-256 webhook signature."""
        if not raw_body or not signature or not secret:
            return False

        computed = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), getattr(hashlib, algorithm, hashlib.sha256)).hexdigest()
        return hmac.compare_digest(computed.lower(), signature.lower())

    def check_replay_and_deduplicate(self, nonce: str, timestamp: float, max_age_seconds: float = 300.0) -> bool:
        """Enforces replay protection and deduplicates incoming webhooks."""
        now = time.time()
        if abs(now - timestamp) > max_age_seconds:
            logger.warning(f"Rejected webhook replay attack: timestamp {timestamp} differs from current time by > {max_age_seconds}s")
            return False

        if nonce in self._processed_nonces:
            logger.warning(f"Rejected duplicate webhook event with nonce: {nonce}")
            return False

        self._processed_nonces[nonce] = now
        return True


webhook_platform = WebhookPlatform()

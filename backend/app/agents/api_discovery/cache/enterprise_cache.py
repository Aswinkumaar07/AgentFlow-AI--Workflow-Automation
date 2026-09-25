import json
import logging
import time
from typing import Any, Dict, List, Optional
from app.agents.api_discovery.config import discovery_config
from app.agents.api_discovery.interfaces import BaseEnterpriseCache
from app.core.config import settings

logger = logging.getLogger("agentflow.api_discovery.cache")


class EnterpriseCache(BaseEnterpriseCache):
    """Enterprise Tier-1 Cache with Redis backend, memory fallback, versioning, and hit telemetry."""

    def __init__(self) -> None:
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._hits = 0
        self._misses = 0
        self._redis_client = None
        self._initialize_redis()

    def _initialize_redis(self) -> None:
        if discovery_config.CACHE_BACKEND == "redis":
            try:
                import redis
                self._redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=1.0)
                self._redis_client.ping()
                logger.info("EnterpriseCache initialized with Redis backend.")
            except Exception as e:
                self._redis_client = None
                logger.info(f"Redis unavailable ({e}). EnterpriseCache using fast in-memory cache.")

    async def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        clean_key = f"api_discovery:v2:{key.strip().lower()}"

        if self._redis_client:
            try:
                val = self._redis_client.get(clean_key)
                if val:
                    self._hits += 1
                    return json.loads(val)
            except Exception as e:
                logger.warning(f"Redis read error: {e}")

        if clean_key in self._memory_cache:
            entry = self._memory_cache[clean_key]
            if time.time() < entry["expires_at"]:
                self._hits += 1
                return entry["data"]
            del self._memory_cache[clean_key]

        self._misses += 1
        return None

    async def set(self, key: str, value: List[Dict[str, Any]], ttl_seconds: int = 3600) -> bool:
        clean_key = f"api_discovery:v2:{key.strip().lower()}"

        if self._redis_client:
            try:
                self._redis_client.setex(clean_key, ttl_seconds, json.dumps(value))
            except Exception as e:
                logger.warning(f"Redis write error: {e}")

        self._memory_cache[clean_key] = {
            "data": value,
            "expires_at": time.time() + ttl_seconds,
        }
        return True

    def get_hit_ratio(self) -> float:
        total = self._hits + self._misses
        return round(self._hits / total, 3) if total > 0 else 1.0

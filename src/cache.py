"""
Timuclaude In-Memory Response Cache
Caches identical requests to save API calls.
LRU eviction with TTL.

For Phase 5: in-memory (simple, no Redis needed).
Phase 6: Redis for production scaling.
"""
import time
from collections import OrderedDict
from typing import Optional, Any
import hashlib


DEFAULT_MAX_SIZE = 1000
DEFAULT_TTL_SECONDS = 3600  # 1 hour


class ResponseCache:
    """LRU cache with TTL for API responses.
    
    Caches identical requests (same model + messages) to avoid
    redundant model calls. Entries expire after TTL.
    """
    
    def __init__(self, max_size: int = DEFAULT_MAX_SIZE, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._hits = 0
        self._misses = 0
    
    def _make_key(self, model: str, messages: list) -> str:
        """Create a cache key from model and messages."""
        # Hash the model + messages for a compact key
        content = f"{model}:{str(messages)}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, model: str, messages: list) -> Optional[str]:
        """Get a cached response. Returns None if not found or expired."""
        key = self._make_key(model, messages)
        
        if key not in self._cache:
            self._misses += 1
            return None
        
        timestamp, value = self._cache[key]
        
        # Check TTL
        if time.time() - timestamp > self.ttl_seconds:
            # Expired
            del self._cache[key]
            self._misses += 1
            return None
        
        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        return value
    
    def set(self, model: str, messages: list, response: str) -> None:
        """Cache a response."""
        key = self._make_key(model, messages)
        
        self._cache[key] = (time.time(), response)
        self._cache.move_to_end(key)
        
        # Evict oldest if over max size
        while len(self._cache) > self.max_size:
            self._cache.popitem(last=False)
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
    
    def stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "ttl_seconds": self.ttl_seconds,
        }
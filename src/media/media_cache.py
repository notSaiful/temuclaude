"""
Temuclaude Media Cache

Extends the existing SemanticResponseCache (from cache.py) for media generation.
Same prompt + same model + same seed + same parameters = same image/video.

Cache key: hash(prompt + model_id + seed + size + other params)
Cache value: {url, model, score, cost, timestamp}

Expected savings: 40-60% (same as LLM cache) — if a user requests the same
prompt twice, the second request is free and instant.
"""

import time
import hashlib
import logging
from typing import Optional, Any
from collections import OrderedDict

logger = logging.getLogger(__name__)

DEFAULT_MAX_SIZE = 1000
DEFAULT_TTL_SECONDS = 3600  # 1 hour (same as LLM cache)


class MediaCache:
    """Hash-based cache for media generation results.

    Cache key: SHA-256 hash of (prompt + model_id + seed + size + params)
    Cache value: dict with url, model, score, cost, timestamp

    The cache is NOT semantic (unlike the LLM cache) because:
      - Image generation is deterministic with the same seed
      - Small prompt changes can produce very different images
      - Semantic matching would risk false positives
    """

    def __init__(
        self,
        max_size: int = DEFAULT_MAX_SIZE,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, dict] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _make_key(
        self,
        prompt: str,
        model_id: str,
        seed: int = None,
        size: str = "1024x1024",
        **extra_params,
    ) -> str:
        """Create a cache key from the generation parameters.

        The key is a hash of all parameters that affect the output.
        """
        # Sort extra params for consistent hashing
        sorted_params = sorted(extra_params.items())
        param_str = f"{prompt}|{model_id}|{seed}|{size}|{sorted_params}"
        return hashlib.sha256(param_str.encode()).hexdigest()

    def get(
        self,
        prompt: str,
        model_id: str,
        seed: int = None,
        size: str = "1024x1024",
        **extra_params,
    ) -> Optional[dict]:
        """Check if a cached result exists for these parameters.

        Returns:
            Cached result dict (with url, model, score) or None if not cached.
        """
        key = self._make_key(prompt, model_id, seed, size, **extra_params)

        if key in self._cache:
            entry = self._cache[key]

            # Check TTL
            if time.time() - entry["timestamp"] > self.ttl_seconds:
                # Expired — remove
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            self._hits += 1

            logger.debug(f"Media cache HIT: {model_id} (key={key[:8]}...)")
            return entry.get("result")

        self._misses += 1
        return None

    def set(
        self,
        prompt: str,
        model_id: str,
        result: dict,
        seed: int = None,
        size: str = "1024x1024",
        **extra_params,
    ):
        """Cache a generation result.

        Args:
            prompt: The prompt used
            model_id: The model that generated
            result: The result dict (url, model, score, cost, etc.)
            seed: Seed used
            size: Image size
            **extra_params: Other parameters
        """
        key = self._make_key(prompt, model_id, seed, size, **extra_params)

        # Evict oldest if at capacity
        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)

        self._cache[key] = {
            "result": result,
            "timestamp": time.time(),
        }

    def get_generation_result(
        self,
        prompt: str,
        tier: str,
        task_type: str,
        media_type: str = "image",
        size: str = "1024x1024",
        **extra_params,
    ) -> Optional[dict]:
        """Check if a complete generation result (from the full pipeline) is cached.

        This caches the FINAL result from the quality gate — including
        the winning model, score, and URL.

        The key includes the tier and task type because different tiers
        produce different quality outputs.
        """
        # For pipeline-level cache, we don't use model_id or seed
        # (those are internal to the pipeline)
        param_str = f"{prompt}|{tier}|{task_type}|{media_type}|{size}|{sorted(extra_params.items())}"
        key = "pipeline_" + hashlib.sha256(param_str.encode()).hexdigest()

        if key in self._cache:
            entry = self._cache[key]
            if time.time() - entry["timestamp"] > self.ttl_seconds:
                del self._cache[key]
                return None

            self._cache.move_to_end(key)
            self._hits += 1
            return entry.get("result")

        return None

    def set_generation_result(
        self,
        prompt: str,
        tier: str,
        task_type: str,
        result: dict,
        media_type: str = "image",
        size: str = "1024x1024",
        **extra_params,
    ):
        """Cache a complete pipeline generation result."""
        param_str = f"{prompt}|{tier}|{task_type}|{media_type}|{size}|{sorted(extra_params.items())}"
        key = "pipeline_" + hashlib.sha256(param_str.encode()).hexdigest()

        while len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)

        self._cache[key] = {
            "result": result,
            "timestamp": time.time(),
        }

    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> dict:
        """Get cache statistics."""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0.0,
            "ttl_seconds": self.ttl_seconds,
        }


# Singleton instance
_media_cache: Optional[MediaCache] = None


def get_media_cache() -> MediaCache:
    """Get the singleton media cache instance."""
    global _media_cache
    if _media_cache is None:
        _media_cache = MediaCache()
    return _media_cache
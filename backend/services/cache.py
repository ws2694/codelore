"""Simple in-memory TTL cache for explore endpoint responses."""

import time
from typing import Any

_cache: dict[str, tuple[float, Any]] = {}

# Default TTL: 10 minutes — data only changes on ingestion
DEFAULT_TTL = 600


def get(key: str) -> Any | None:
    """Return cached value if it exists and hasn't expired."""
    entry = _cache.get(key)
    if entry is None:
        return None
    expires_at, value = entry
    if time.monotonic() > expires_at:
        _cache.pop(key, None)
        return None
    return value


def put(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Store a value with a TTL (in seconds)."""
    _cache[key] = (time.monotonic() + ttl, value)


def invalidate_all() -> None:
    """Clear entire cache — call after ingestion."""
    _cache.clear()


def invalidate_prefix(prefix: str) -> None:
    """Clear all cache entries whose key starts with prefix."""
    to_delete = [k for k in _cache if k.startswith(prefix)]
    for k in to_delete:
        del _cache[k]

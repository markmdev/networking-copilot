"""Simple Redis-backed caching helpers for lookup responses."""

from __future__ import annotations

import json
import os
from hashlib import sha256
from typing import Any, Dict, Optional

import redis

_CACHE_TTL_SECONDS = 60 * 60 * 24  # 24 hours
_redis_client: Optional[redis.Redis] = None
_redis_initialized = False


def _get_redis_client() -> Optional[redis.Redis]:
    global _redis_client, _redis_initialized

    if _redis_initialized:
        return _redis_client

    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    try:
        client = redis.Redis.from_url(url, decode_responses=True)
        client.ping()
        _redis_client = client
    except redis.exceptions.RedisError:
        _redis_client = None

    _redis_initialized = True
    return _redis_client


def _build_lookup_cache_key(first_name: str, last_name: str) -> str:
    payload = {
        "first": first_name.strip().lower(),
        "last": last_name.strip().lower(),
    }
    digest = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"lookup:{digest}"


def get_cached_lookup(first_name: str, last_name: str) -> Optional[Dict[str, Any]]:
    client = _get_redis_client()
    if client is None:
        return None

    key = _build_lookup_cache_key(first_name, last_name)
    try:
        value = client.get(key)
    except redis.exceptions.RedisError:
        return None

    if not value:
        return None

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None


def set_cached_lookup(first_name: str, last_name: str, result: Dict[str, Any]) -> None:
    client = _get_redis_client()
    if client is None:
        return

    key = _build_lookup_cache_key(first_name, last_name)
    try:
        client.setex(key, _CACHE_TTL_SECONDS, json.dumps(result))
    except redis.exceptions.RedisError:
        return

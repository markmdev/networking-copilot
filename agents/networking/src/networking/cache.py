"""Simple Redis-backed caching helpers for lookup responses."""

from __future__ import annotations

import json
import os
from datetime import datetime
from hashlib import sha256
from typing import Any, Dict, List, Optional
from uuid import uuid4

import redis

_CACHE_TTL_SECONDS = 60 * 60 * 24  # 24 hours
_redis_client: Optional[redis.Redis] = None
_redis_initialized = False

PEOPLE_INDEX_KEY = "people:index"
PERSON_DATA_KEY = "people:data:{id}"


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


def save_person_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Persist a person record in Redis and return it with metadata."""

    person_id = str(uuid4())
    stored_record = {
        "id": person_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        **record,
    }

    client = _get_redis_client()
    if client is None:
        return stored_record

    key = PERSON_DATA_KEY.format(id=person_id)
    try:
        pipe = client.pipeline()
        pipe.set(key, json.dumps(stored_record))
        pipe.lpush(PEOPLE_INDEX_KEY, person_id)
        pipe.execute()
    except redis.exceptions.RedisError:
        return stored_record

    return stored_record


def list_person_records(limit: int = 50) -> List[Dict[str, Any]]:
    client = _get_redis_client()
    if client is None:
        return []

    try:
        ids = client.lrange(PEOPLE_INDEX_KEY, 0, max(limit - 1, 0))
    except redis.exceptions.RedisError:
        return []

    if not ids:
        return []

    try:
        pipe = client.pipeline()
        for pid in ids:
            pipe.get(PERSON_DATA_KEY.format(id=pid))
        raw_records = pipe.execute()
    except redis.exceptions.RedisError:
        return []

    records: List[Dict[str, Any]] = []
    for raw in raw_records:
        if not raw:
            continue
        try:
            records.append(json.loads(raw))
        except json.JSONDecodeError:
            continue

    return records


def get_person_record(person_id: str) -> Optional[Dict[str, Any]]:
    client = _get_redis_client()
    if client is None:
        return None

    try:
        raw = client.get(PERSON_DATA_KEY.format(id=person_id))
    except redis.exceptions.RedisError:
        return None

    if not raw:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None

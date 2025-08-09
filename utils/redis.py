from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Tuple

import redis as _redis


DEFAULT_TTL_SECONDS = int(os.environ.get("THERAPY_SESSION_TTL", 60 * 60 * 24 * 3))  # 3 days
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
SENSITIVE_KEYS = {
    k.strip().lower()
    for k in os.environ.get(
        "THERAPY_SENSITIVE_KEYS",
        "token,authorization,password,secret,api_key,apikey,bearer,session,cookie",
    ).split(",")
}


class _InMemoryPipeline:
    def __init__(self, client: "_InMemoryRedis") -> None:
        self.client = client
        self.ops: List[Tuple[str, Tuple[Any, ...]]] = []

    # Collect commands
    def set(self, key: str, value: str) -> "_InMemoryPipeline":
        self.ops.append(("set", (key, value)))
        return self

    def expire(self, key: str, ttl: int) -> "_InMemoryPipeline":
        self.ops.append(("expire", (key, ttl)))
        return self

    def delete(self, key: str) -> "_InMemoryPipeline":
        self.ops.append(("delete", (key,)))
        return self

    def rpush(self, key: str, value: str) -> "_InMemoryPipeline":
        self.ops.append(("rpush", (key, value)))
        return self

    def ltrim(self, key: str, start: int, end: int) -> "_InMemoryPipeline":
        self.ops.append(("ltrim", (key, start, end)))
        return self

    def execute(self) -> None:
        for name, args in self.ops:
            getattr(self.client, name)(*args)
        self.ops.clear()


class _InMemoryRedis:
    def __init__(self) -> None:
        self._kv: Dict[str, str] = {}
        self._lists: Dict[str, List[str]] = {}
        self._expiry: Dict[str, float] = {}

    # housekeeping
    def _purge_if_expired(self, key: str) -> None:
        exp = self._expiry.get(key)
        if exp is not None and time.time() > exp:
            self._kv.pop(key, None)
            self._lists.pop(key, None)
            self._expiry.pop(key, None)

    # Core API used by session_store
    def get(self, key: str) -> str | None:
        self._purge_if_expired(key)
        return self._kv.get(key)

    def set(self, key: str, value: str) -> bool:
        self._kv[key] = value
        return True

    def delete(self, key: str) -> int:
        self._kv.pop(key, None)
        self._lists.pop(key, None)
        self._expiry.pop(key, None)
        return 1

    def expire(self, key: str, ttl: int) -> bool:
        self._expiry[key] = time.time() + ttl
        return True

    def pipeline(self) -> _InMemoryPipeline:
        return _InMemoryPipeline(self)

    # List ops for mood history
    def rpush(self, key: str, value: str) -> int:
        self._purge_if_expired(key)
        self._lists.setdefault(key, []).append(value)
        return len(self._lists[key])

    def lrange(self, key: str, start: int, end: int) -> List[str]:
        self._purge_if_expired(key)
        arr = self._lists.get(key, [])
        # emulate Redis lrange inclusive end, negative indices supported
        n = len(arr)
        if start < 0:
            start = max(0, n + start)
        if end < 0:
            end = n + end
        end = min(n - 1, end) if n > 0 else -1
        if end < start:
            return []
        return arr[start : end + 1]

    def llen(self, key: str) -> int:
        self._purge_if_expired(key)
        return len(self._lists.get(key, []))

    def ltrim(self, key: str, start: int, end: int) -> None:
        self._purge_if_expired(key)
        arr = self._lists.get(key)
        if arr is None:
            return
        n = len(arr)
        if start < 0:
            start = max(0, n + start)
        if end < 0:
            end = n + end
        end = min(n - 1, end) if n > 0 else -1
        if end < start:
            self._lists[key] = []
        else:
            self._lists[key] = arr[start : end + 1]

    def ping(self) -> bool:  # used by tests
        return True


def get_redis_client(url: str | None = None) -> Any:
    target = (url or REDIS_URL).strip()
    if target.startswith("memory://") or os.environ.get("THERAPY_FAKE_REDIS", "0").lower() in ("1", "true", "yes"):  # type: ignore
        return _InMemoryRedis()
    return _redis.from_url(target, decode_responses=True)


def scrub_context(ctx: Dict[str, Any] | None) -> Dict[str, Any]:
    if not ctx:
        return {}
    return {k: v for k, v in ctx.items() if k.lower() not in SENSITIVE_KEYS}

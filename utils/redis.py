from __future__ import annotations

import os
from typing import Any, Dict

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


def get_redis_client(url: str | None = None) -> _redis.Redis:
    return _redis.from_url(url or REDIS_URL, decode_responses=True)


def scrub_context(ctx: Dict[str, Any] | None) -> Dict[str, Any]:
    if not ctx:
        return {}
    return {k: v for k, v in ctx.items() if k.lower() not in SENSITIVE_KEYS}

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from .models import TherapySession as ModelTherapySession, SessionState
from utils.redis import (
    get_redis_client,
    scrub_context,
    DEFAULT_TTL_SECONDS,
    REDIS_URL,
)


class RedisSessionManager:
    """Redis-backed session manager for therapy sessions and mood history.

    Persists Pydantic TherapySession models as JSON.
    """

    def __init__(self, redis_url: str | None = None, ttl_seconds: int | None = None) -> None:
        self.redis_url = redis_url or REDIS_URL
        self.ttl = ttl_seconds or DEFAULT_TTL_SECONDS
        self.client = get_redis_client(self.redis_url)

    # Keys
    def _session_key(self, user_id: str) -> str:
        return f"therapy_session:{user_id}"

    def _moodlog_key(self, user_id: str) -> str:
        return f"mood_log:{user_id}"

    # CRUD for session
    def get_session(self, user_id: str) -> ModelTherapySession:
        key = self._session_key(user_id)
        data = self.client.get(key)
        if not data:
            return ModelTherapySession(user_id=user_id)
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            return ModelTherapySession(user_id=user_id)
        try:
            # pydantic v2 validation
            return ModelTherapySession.model_validate(payload)
        except Exception:
            # fallback minimal recovery
            return ModelTherapySession(user_id=user_id)

    def save_session(self, session: ModelTherapySession) -> None:
        # Update timestamp (timezone-aware)
        session.updated_at = session.updated_at.__class__.fromtimestamp(time.time(), tz=session.updated_at.tzinfo)
        key = self._session_key(session.user_id)
        # Scrub context before persisting (do not mutate original session)
        dump_dict = session.model_dump(mode="json")
        dump_dict["context"] = scrub_context(dump_dict.get("context"))
        payload = json.dumps(dump_dict)
        pipe = self.client.pipeline()
        pipe.set(key, payload)
        pipe.expire(key, self.ttl)
        pipe.execute()

    def delete_session(self, user_id: str) -> None:
        key = self._session_key(user_id)
        self.client.delete(key)

    # History helpers
    def add_to_history(
        self,
        user_id: str,
        command: str,
        parameter: Optional[str],
        result: Dict[str, Any] | List[Any] | str | None,
    ) -> None:
        key = self._moodlog_key(user_id)
        entry = {
            "ts": time.time(),
            "command": command,
            "parameter": parameter,
            "result": result
            if isinstance(result, (dict, list))
            else ({"text": str(result)} if result is not None else None),
        }
        pipe = self.client.pipeline()
        pipe.rpush(key, json.dumps(entry))
        pipe.expire(key, self.ttl)
        pipe.execute()

    def get_mood_history(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        key = self._moodlog_key(user_id)
        length = self.client.llen(key)
        if length == 0:
            return []
        start = max(0, length - limit)
        items = self.client.lrange(key, start, -1)
        out: List[Dict[str, Any]] = []
        for item in items:
            try:
                out.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        return out


# Convenience factory (singleton)
_redis_manager: Optional[RedisSessionManager] = None

def get_redis_session_manager() -> RedisSessionManager:
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisSessionManager()
    return _redis_manager

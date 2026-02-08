from unittest.mock import MagicMock

import redis.asyncio as aioredis


class LoopPrevention:
    def __init__(self, redis_client: aioredis.Redis | MagicMock | None = None):
        self._redis = redis_client
        self._key_prefix = "posted_comments"
        self._ttl_seconds = 3600

    async def track_posted_comment(self, comment_id: str) -> None:
        if self._redis:
            key = f"{self._key_prefix}:{comment_id}"
            await self._redis.setex(key, self._ttl_seconds, "1")

    async def is_own_comment(self, comment_id: str) -> bool:
        if not self._redis:
            return False
        key = f"{self._key_prefix}:{comment_id}"
        result = await self._redis.get(key)
        return result is not None

    def get_key(self, comment_id: str) -> str:
        return f"{self._key_prefix}:{comment_id}"

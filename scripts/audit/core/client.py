import logging
from typing import Self

import httpx
import redis.asyncio as aioredis

from scripts.audit.config import AuditConfig

logger = logging.getLogger(__name__)


class AuditClient:
    def __init__(self, config: AuditConfig) -> None:
        self.config = config
        self._http: httpx.AsyncClient | None = None
        self._redis: aioredis.Redis | None = None

    async def connect(self) -> None:
        self._http = httpx.AsyncClient(timeout=30.0)
        self._redis = aioredis.from_url(
            self.config.redis_url,
            decode_responses=True,
        )

    async def close(self) -> None:
        if self._http:
            await self._http.aclose()
            self._http = None
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(
        self, exc_type: type | None, exc_val: Exception | None, exc_tb: object
    ) -> None:
        await self.close()

    @property
    def http(self) -> httpx.AsyncClient:
        if not self._http:
            raise RuntimeError("AuditClient not connected")
        return self._http

    @property
    def redis(self) -> aioredis.Redis:
        if not self._redis:
            raise RuntimeError("AuditClient not connected")
        return self._redis

    async def post_github_api(self, path: str, json: dict) -> httpx.Response:
        url = f"{self.config.github_api_url}{path}"
        logger.info("post_github_api", extra={"url": url})
        response = await self.http.post(url, json=json)
        response.raise_for_status()
        return response

    async def post_jira_api(self, path: str, json: dict) -> httpx.Response:
        url = f"{self.config.jira_api_url}{path}"
        logger.info("post_jira_api", extra={"url": url})
        response = await self.http.post(url, json=json)
        response.raise_for_status()
        return response

    async def post_slack_api(self, path: str, json: dict) -> httpx.Response:
        url = f"{self.config.slack_api_url}{path}"
        logger.info("post_slack_api", extra={"url": url})
        response = await self.http.post(url, json=json)
        response.raise_for_status()
        return response

    async def get_github_api(self, path: str) -> httpx.Response:
        url = f"{self.config.github_api_url}{path}"
        response = await self.http.get(url)
        response.raise_for_status()
        return response

    async def get_jira_api(self, path: str) -> httpx.Response:
        url = f"{self.config.jira_api_url}{path}"
        response = await self.http.get(url)
        response.raise_for_status()
        return response

    async def get_conversation_by_flow(self, flow_id: str) -> dict:
        url = f"{self.config.dashboard_api_url}/api/conversations/by-flow/{flow_id}"
        logger.info("get_conversation_by_flow", extra={"flow_id": flow_id})
        response = await self.http.get(url)
        response.raise_for_status()
        return response.json()

    async def get_conversation_messages(self, conversation_id: str) -> list[dict]:
        url = f"{self.config.dashboard_api_url}/api/conversations/{conversation_id}/messages"
        logger.info("get_conversation_messages", extra={"conversation_id": conversation_id})
        response = await self.http.get(url)
        response.raise_for_status()
        return response.json()

    async def get_task_logs(self, task_id: str) -> dict:
        url = f"{self.config.task_logger_url}/tasks/{task_id}/logs"
        logger.info("get_task_logs", extra={"task_id": task_id})
        response = await self.http.get(url)
        response.raise_for_status()
        return response.json()

    async def check_health(self, service_url: str) -> bool:
        try:
            response = await self.http.get(f"{service_url}/health", timeout=5.0)
            if response.status_code == 200:
                return True
            response = await self.http.get(f"{service_url}/api/health", timeout=5.0)
            return response.status_code == 200
        except (httpx.HTTPError, httpx.TimeoutException):
            return False

    async def clear_dedup_key(self, key_prefix: str, artifact_id: str) -> bool:
        key = f"{key_prefix}:{artifact_id}"
        logger.info("clear_dedup_key", extra={"key": key})
        deleted = await self.redis.delete(key)
        return deleted > 0

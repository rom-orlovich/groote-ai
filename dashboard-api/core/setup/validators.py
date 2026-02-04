import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

import httpx
import structlog
from pydantic import BaseModel, ConfigDict

logger = structlog.get_logger()

VALIDATION_TIMEOUT = 10.0
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0


async def with_retry(
    fn: Callable[[], Coroutine[Any, Any, "ValidationResult"]],
    service: str,
) -> "ValidationResult":
    last_error = ""
    for attempt in range(MAX_RETRIES):
        result = await fn()
        if result.success or not _is_transient_error(result.message):
            return result
        last_error = result.message
        if attempt < MAX_RETRIES - 1:
            delay = RETRY_BACKOFF_BASE * (2**attempt)
            logger.info(
                "validation_retry",
                service=service,
                attempt=attempt + 1,
                delay=delay,
            )
            await asyncio.sleep(delay)
    return ValidationResult(
        service=service,
        success=False,
        message=f"Failed after {MAX_RETRIES} attempts: {last_error}",
    )


def _is_transient_error(message: str) -> bool:
    transient_indicators = ["Connection error", "timeout", "Temporary", "503", "502", "429"]
    return any(indicator.lower() in message.lower() for indicator in transient_indicators)


class ValidationResult(BaseModel):
    model_config = ConfigDict(strict=True)

    service: str
    success: bool
    message: str
    details: dict[str, str] | None = None


async def validate_github(token: str) -> ValidationResult:
    async def _attempt() -> ValidationResult:
        try:
            async with httpx.AsyncClient(timeout=VALIDATION_TIMEOUT) as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    return ValidationResult(
                        service="github",
                        success=True,
                        message=f"Connected as {data.get('login', 'unknown')}",
                        details={"login": data.get("login", ""), "name": data.get("name", "")},
                    )
                return ValidationResult(
                    service="github",
                    success=False,
                    message=f"Authentication failed (HTTP {response.status_code})",
                )
        except httpx.RequestError as e:
            return ValidationResult(
                service="github", success=False, message=f"Connection error: {e!s}"
            )

    return await with_retry(_attempt, "github")


async def validate_jira(url: str, email: str, token: str) -> ValidationResult:
    async def _attempt() -> ValidationResult:
        try:
            api_url = url.rstrip("/")
            async with httpx.AsyncClient(timeout=VALIDATION_TIMEOUT) as client:
                response = await client.get(
                    f"{api_url}/rest/api/3/myself",
                    auth=(email, token),
                    headers={"Accept": "application/json"},
                )
                if response.status_code == 200:
                    data = response.json()
                    return ValidationResult(
                        service="jira",
                        success=True,
                        message=f"Connected as {data.get('displayName', 'unknown')}",
                        details={
                            "display_name": data.get("displayName", ""),
                            "email": data.get("emailAddress", ""),
                        },
                    )
                return ValidationResult(
                    service="jira",
                    success=False,
                    message=f"Authentication failed (HTTP {response.status_code})",
                )
        except httpx.RequestError as e:
            return ValidationResult(
                service="jira", success=False, message=f"Connection error: {e!s}"
            )

    return await with_retry(_attempt, "jira")


async def validate_slack(bot_token: str) -> ValidationResult:
    async def _attempt() -> ValidationResult:
        try:
            async with httpx.AsyncClient(timeout=VALIDATION_TIMEOUT) as client:
                response = await client.post(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {bot_token}"},
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return ValidationResult(
                            service="slack",
                            success=True,
                            message=f"Connected to workspace: {data.get('team', 'unknown')}",
                            details={"team": data.get("team", ""), "user": data.get("user", "")},
                        )
                    return ValidationResult(
                        service="slack",
                        success=False,
                        message=f"Slack error: {data.get('error', 'unknown')}",
                    )
                return ValidationResult(
                    service="slack",
                    success=False,
                    message=f"HTTP error {response.status_code}",
                )
        except httpx.RequestError as e:
            return ValidationResult(
                service="slack", success=False, message=f"Connection error: {e!s}"
            )

    return await with_retry(_attempt, "slack")


async def validate_sentry(auth_token: str) -> ValidationResult:
    async def _attempt() -> ValidationResult:
        try:
            async with httpx.AsyncClient(timeout=VALIDATION_TIMEOUT) as client:
                response = await client.get(
                    "https://sentry.io/api/0/",
                    headers={"Authorization": f"Bearer {auth_token}"},
                )
                if response.status_code == 200:
                    return ValidationResult(
                        service="sentry",
                        success=True,
                        message="Connected to Sentry API",
                    )
                return ValidationResult(
                    service="sentry",
                    success=False,
                    message=f"Authentication failed (HTTP {response.status_code})",
                )
        except httpx.RequestError as e:
            return ValidationResult(
                service="sentry", success=False, message=f"Connection error: {e!s}"
            )

    return await with_retry(_attempt, "sentry")


async def validate_anthropic(api_key: str) -> ValidationResult:
    if not api_key.strip():
        return ValidationResult(
            service="anthropic",
            success=True,
            message="Using credential-based authentication (~/.anthropic)",
        )

    async def _attempt() -> ValidationResult:
        try:
            async with httpx.AsyncClient(timeout=VALIDATION_TIMEOUT) as client:
                response = await client.get(
                    "https://api.anthropic.com/v1/models",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                if response.status_code == 200:
                    return ValidationResult(
                        service="anthropic",
                        success=True,
                        message="Anthropic API key is valid",
                    )
                return ValidationResult(
                    service="anthropic",
                    success=False,
                    message=f"Authentication failed (HTTP {response.status_code})",
                )
        except httpx.RequestError as e:
            return ValidationResult(
                service="anthropic", success=False, message=f"Connection error: {e!s}"
            )

    return await with_retry(_attempt, "anthropic")


VALIDATOR_MAP: dict[str, str] = {
    "github": "validate_github",
    "jira": "validate_jira",
    "slack": "validate_slack",
    "sentry": "validate_sentry",
    "anthropic": "validate_anthropic",
}

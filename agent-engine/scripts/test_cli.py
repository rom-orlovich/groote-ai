#!/usr/bin/env python3

import asyncio
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import structlog

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from typing import TYPE_CHECKING

from cli.factory import get_cli_runner
from db import ensure_tables, get_hostname, get_provider, get_session, upsert_instance

if TYPE_CHECKING:
    from cli.base import CLIResult

logger = structlog.get_logger()

_redis_client = None


async def get_redis():
    global _redis_client
    if _redis_client is None:
        import redis.asyncio as aioredis

        redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
        _redis_client = aioredis.from_url(redis_url, decode_responses=True)
    return _redis_client


async def publish_status(
    provider: str,
    step: str,
    status: str,
    detail: str = "",
    version: str = "",
):
    try:
        r = await get_redis()
        payload = json.dumps(
            {
                "provider": provider,
                "step": step,
                "status": status,
                "detail": detail,
                "version": version,
                "hostname": get_hostname(),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        await r.publish("cli:status", payload)
        await r.set("cli:startup_status", payload)
        logger.info("cli_status_published", step=step, status=status)
    except Exception as e:
        logger.warning("cli_status_publish_failed", error=str(e))


def check_credentials(provider: str) -> tuple[bool, str]:
    if provider == "claude":
        creds_path = Path.home() / ".claude" / ".credentials.json"
        if creds_path.exists():
            logger.info("claude_credentials_found", path=str(creds_path))
            return True, str(creds_path)
        if os.environ.get("ANTHROPIC_API_KEY"):
            logger.info("claude_api_key_found")
            return True, "api_key"
    elif provider == "cursor":
        if os.environ.get("CURSOR_API_KEY"):
            logger.info("cursor_api_key_found")
            return True, "api_key"

    logger.warning("no_credentials_found", provider=provider)
    return False, "missing"


def check_token_expiry(provider: str) -> tuple[bool, str]:
    if provider != "claude":
        return True, "n/a"

    creds_path = Path.home() / ".claude" / ".credentials.json"
    if not creds_path.exists():
        return False, "no_credentials_file"

    try:
        creds_data = json.loads(creds_path.read_text())
        oauth = creds_data.get("claudeAiOauth", creds_data)
        expires_at = oauth.get("expiresAt") or oauth.get("expires_at", 0)
        now_ms = int(datetime.now(UTC).timestamp() * 1000)

        if now_ms >= expires_at:
            logger.warning("oauth_token_expired")
            return False, "expired"

        remaining_hours = (expires_at - now_ms) / 1000 / 3600
        logger.info("oauth_token_valid", expires_in_hours=round(remaining_hours, 1))
        return True, f"{remaining_hours:.1f}h remaining"
    except Exception as e:
        logger.warning("token_expiry_check_failed", error=str(e))
        return False, str(e)


async def test_version(provider: str) -> tuple[bool, str]:
    cmd = "claude" if provider == "claude" else "agent"
    try:
        process = await asyncio.create_subprocess_exec(
            cmd,
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=30.0)

        if process.returncode == 0:
            version = stdout.decode().strip()
            logger.info("version_check_passed", provider=provider, version=version)
            return True, version

        error = stderr.decode().strip() or stdout.decode().strip()
        logger.warning("version_check_failed", provider=provider, error=error)
        return False, error
    except Exception as e:
        logger.error("version_check_error", provider=provider, error=str(e))
        return False, str(e)


async def test_prompt(provider: str) -> tuple[bool, str]:
    try:
        runner = get_cli_runner()
        queue: asyncio.Queue[str | None] = asyncio.Queue()

        result: CLIResult = await runner.run(
            prompt="Say 'CLI test successful' and nothing else",
            working_dir=Path("/tmp"),
            output_queue=queue,
            task_id="test-cli",
            timeout_seconds=60,
        )

        if result.success:
            logger.info("prompt_test_passed", provider=provider, output=result.output[:200])
            return True, "passed"

        logger.warning("prompt_test_failed", provider=provider, error=result.error)
        return False, result.error or "unknown_error"
    except Exception as e:
        logger.error("prompt_test_error", provider=provider, error=str(e))
        return False, str(e)


async def log_to_db(provider: str, version: str, status: str):
    from sqlalchemy import text

    try:
        async with get_session() as session:
            if session is None:
                return

            await ensure_tables(session)

            hostname = get_hostname()
            await session.execute(
                text("""
                    INSERT INTO cli_health (provider, version, status, hostname, checked_at)
                    VALUES (:provider, :version, :status, :hostname, :checked_at)
                """),
                {
                    "provider": provider,
                    "version": version,
                    "status": status,
                    "hostname": hostname,
                    "checked_at": datetime.now(UTC),
                },
            )

            await upsert_instance(session, provider, hostname, version)
            await session.commit()

        logger.info("cli_status_logged", provider=provider, version=version, status=status)
    except Exception as e:
        logger.warning("db_logging_failed", error=str(e))


async def cleanup_redis():
    if _redis_client:
        await _redis_client.aclose()


async def main() -> int:
    provider = get_provider()
    logger.info("starting_cli_check", provider=provider)

    await publish_status(provider, "credentials", "checking")

    creds_ok, creds_detail = check_credentials(provider)
    if not creds_ok:
        await publish_status(provider, "credentials", "failed", creds_detail)
        await log_to_db(provider, "unknown", "no_credentials")
        print(f"CLI check: FAIL - no credentials ({creds_detail})")
        await cleanup_redis()
        return 1

    await publish_status(provider, "credentials", "ok", creds_detail)

    expiry_ok, expiry_detail = check_token_expiry(provider)
    if not expiry_ok:
        await publish_status(provider, "auth", "expired", expiry_detail)
    else:
        await publish_status(provider, "auth", "ok", expiry_detail)

    await publish_status(provider, "version", "checking")
    version_ok, version = await test_version(provider)
    if not version_ok:
        await publish_status(provider, "version", "failed", version, version)
        await log_to_db(provider, "unknown", "version_failed")
        print(f"CLI check: FAIL - version check failed ({version})")
        await cleanup_redis()
        return 1

    await publish_status(provider, "version", "ok", version, version)

    prompt_ok = True
    if expiry_ok:
        await publish_status(provider, "prompt_test", "checking", version=version)
        prompt_ok, prompt_detail = await test_prompt(provider)
        if prompt_ok:
            await publish_status(provider, "prompt_test", "ok", "passed", version)
        else:
            await publish_status(provider, "prompt_test", "failed", prompt_detail, version)
    else:
        logger.info("skipping_prompt_test", reason="token_expired")

    if expiry_ok and prompt_ok:
        status = "healthy"
    elif not expiry_ok:
        status = "token_expired"
    else:
        status = "prompt_failed"

    await publish_status(provider, "ready", status, version=version)
    await log_to_db(provider, version, status)

    print(f"CLI check: provider={provider} version={version} auth={expiry_detail} status={status}")
    await cleanup_redis()
    return 0 if version_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

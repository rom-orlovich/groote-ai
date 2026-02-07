#!/usr/bin/env python3
"""CLI instance heartbeat - updates last_heartbeat every 30 seconds."""

import asyncio
import signal
import sys
from datetime import UTC, datetime
from pathlib import Path

import structlog
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).parent))

from db import get_hostname, get_provider, get_session, upsert_instance

logger = structlog.get_logger()

shutdown_flag = False


def signal_handler(signum, frame):
    global shutdown_flag
    logger.info("shutdown_signal_received", signal=signum)
    shutdown_flag = True


async def update_heartbeat(hostname: str, provider: str):
    try:
        async with get_session() as session:
            if session is None:
                return

            result = await session.execute(
                text("""
                    UPDATE cli_instances
                    SET last_heartbeat = :heartbeat
                    WHERE hostname = :hostname AND active = true
                """),
                {"heartbeat": datetime.now(UTC), "hostname": hostname},
            )

            if result.rowcount == 0:
                await upsert_instance(session, provider, hostname)

            await session.commit()

        logger.debug("heartbeat_updated", hostname=hostname)
    except Exception as e:
        logger.warning("heartbeat_failed", error=str(e))


async def mark_inactive(hostname: str):
    try:
        async with get_session() as session:
            if session is None:
                return

            await session.execute(
                text("""
                    UPDATE cli_instances
                    SET active = false, last_heartbeat = :heartbeat
                    WHERE hostname = :hostname
                """),
                {"heartbeat": datetime.now(UTC), "hostname": hostname},
            )
            await session.commit()

        logger.info("instance_marked_inactive", hostname=hostname)
    except Exception as e:
        logger.warning("failed_to_mark_inactive", error=str(e))


async def main():
    global shutdown_flag

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    hostname = get_hostname()
    provider = get_provider()

    logger.info("heartbeat_started", interval=30)

    try:
        while not shutdown_flag:
            await update_heartbeat(hostname, provider)
            await asyncio.sleep(30)
    except Exception as e:
        logger.error("heartbeat_error", error=str(e))
    finally:
        logger.info("heartbeat_stopping")
        await mark_inactive(hostname)
        logger.info("heartbeat_stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("heartbeat_interrupted")
        sys.exit(0)

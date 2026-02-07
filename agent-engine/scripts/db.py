#!/usr/bin/env python3
"""Shared DB helpers for CLI scripts."""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = structlog.get_logger()

_engine = None
_session_factory = None


def _get_session_factory():
    global _engine, _session_factory
    if _session_factory is None:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            return None
        _engine = create_async_engine(db_url, echo=False)
        _session_factory = sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _session_factory


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession | None, None]:
    factory = _get_session_factory()
    if factory is None:
        logger.warning("no_database_url")
        yield None
        return
    async with factory() as session:
        yield session


def get_hostname() -> str:
    return os.environ.get("HOSTNAME", "unknown")


def get_provider() -> str:
    return os.environ.get("CLI_PROVIDER", "claude").lower()


async def ensure_tables(session: AsyncSession):
    await session.execute(
        text("""
        CREATE TABLE IF NOT EXISTS cli_health (
            id SERIAL PRIMARY KEY,
            provider VARCHAR(50) NOT NULL,
            version VARCHAR(100),
            status VARCHAR(50) NOT NULL,
            hostname VARCHAR(255),
            checked_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    )
    await session.execute(
        text("""
        CREATE TABLE IF NOT EXISTS cli_instances (
            id SERIAL PRIMARY KEY,
            provider VARCHAR(50) NOT NULL,
            version VARCHAR(100),
            hostname VARCHAR(255) UNIQUE NOT NULL,
            container_id VARCHAR(255),
            active BOOLEAN DEFAULT true,
            started_at TIMESTAMPTZ DEFAULT NOW(),
            last_heartbeat TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    )


async def upsert_instance(session: AsyncSession, provider: str, hostname: str, version: str | None = None):
    params = {"provider": provider, "hostname": hostname, "version": version}
    await session.execute(
        text("""
            INSERT INTO cli_instances
                (provider, version, hostname, container_id, active, started_at, last_heartbeat)
            VALUES (:provider, :version, :hostname, :hostname, true, NOW(), NOW())
            ON CONFLICT (hostname)
            DO UPDATE SET
                provider = EXCLUDED.provider,
                version = COALESCE(EXCLUDED.version, cli_instances.version),
                active = true,
                started_at = NOW(),
                last_heartbeat = NOW()
        """),
        params,
    )

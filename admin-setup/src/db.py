import json
from datetime import UTC, datetime

import structlog
from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = structlog.get_logger()

_engine = None
_session_factory = None


class Base(DeclarativeBase):
    pass


class AdminSetupState(Base):
    __tablename__ = "setup_state"

    id = Column(String(50), primary_key=True, default="admin")
    is_complete = Column(Boolean, nullable=False, default=False)
    current_step = Column(String(50), nullable=False, default="welcome")
    completed_steps = Column(Text, nullable=False, default="[]")
    skipped_steps = Column(Text, nullable=False, default="[]")
    progress_percent = Column(Float, nullable=False, default=0.0)
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def get_completed_steps(self) -> list[str]:
        return json.loads(self.completed_steps) if self.completed_steps else []

    def set_completed_steps(self, steps: list[str]) -> None:
        self.completed_steps = json.dumps(steps)

    def get_skipped_steps(self) -> list[str]:
        return json.loads(self.skipped_steps) if self.skipped_steps else []

    def set_skipped_steps(self, steps: list[str]) -> None:
        self.skipped_steps = json.dumps(steps)


class AdminSetupConfig(Base):
    __tablename__ = "setup_config"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    is_sensitive = Column(Boolean, nullable=False, default=False)
    display_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    scope = Column(String(20), nullable=False, default="admin")


def init_engine(database_url: str) -> None:
    global _engine, _session_factory
    _engine = create_async_engine(database_url, echo=False)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    logger.info("database_engine_initialized", url=database_url.split("@")[-1])


async def create_tables() -> None:
    if _engine is None:
        raise RuntimeError("Engine not initialized. Call init_engine first.")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")


async def get_db():
    if _session_factory is None:
        raise RuntimeError("Session factory not initialized. Call init_engine first.")
    async with _session_factory() as session:
        yield session

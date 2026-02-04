from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text

from core.database.models import Base


def utc_now():
    return datetime.now(UTC)


class SetupConfigDB(Base):
    __tablename__ = "setup_config"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, index=True)
    is_sensitive = Column(Boolean, default=False, nullable=False)
    display_name = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class SetupStateDB(Base):
    __tablename__ = "setup_state"

    id = Column(String(50), primary_key=True, default="singleton")
    is_complete = Column(Boolean, default=False, nullable=False)
    current_step = Column(String(50), default="welcome", nullable=False)
    completed_steps = Column(Text, default="[]", nullable=False)
    skipped_steps = Column(Text, default="[]", nullable=False)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    progress_percent = Column(Float, default=0.0, nullable=False)

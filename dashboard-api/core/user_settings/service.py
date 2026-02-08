import uuid
from datetime import UTC, datetime

import structlog
from core.setup.encryption import decrypt_value, encrypt_value
from core.setup.models import UserSettingsDB
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


async def save_user_setting(
    db: AsyncSession,
    user_id: str,
    category: str,
    key: str,
    value: str,
    is_sensitive: bool = False,
) -> UserSettingsDB:
    stored_value = encrypt_value(value) if is_sensitive else value
    result = await db.execute(
        select(UserSettingsDB).where(
            (UserSettingsDB.user_id == user_id)
            & (UserSettingsDB.category == category)
            & (UserSettingsDB.key == key)
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.value = stored_value
        existing.is_sensitive = is_sensitive
        existing.updated_at = datetime.now(UTC)
        db.add(existing)
    else:
        setting = UserSettingsDB(
            id=str(uuid.uuid4()),
            user_id=user_id,
            category=category,
            key=key,
            value=stored_value,
            is_sensitive=is_sensitive,
        )
        db.add(setting)

    await db.commit()
    return existing or setting


async def get_user_setting(
    db: AsyncSession,
    user_id: str,
    category: str,
    key: str,
) -> str | None:
    result = await db.execute(
        select(UserSettingsDB).where(
            (UserSettingsDB.user_id == user_id)
            & (UserSettingsDB.category == category)
            & (UserSettingsDB.key == key)
        )
    )
    setting = result.scalar_one_or_none()
    if not setting or setting.value is None:
        return None
    return decrypt_value(setting.value) if setting.is_sensitive else setting.value


async def get_user_settings_by_category(
    db: AsyncSession,
    user_id: str,
    category: str,
) -> list[dict[str, str | bool]]:
    result = await db.execute(
        select(UserSettingsDB).where(
            (UserSettingsDB.user_id == user_id) & (UserSettingsDB.category == category)
        )
    )
    settings = result.scalars().all()
    return [
        {
            "key": s.key,
            "value": decrypt_value(s.value) if s.is_sensitive and s.value else s.value,
            "is_sensitive": s.is_sensitive,
        }
        for s in settings
    ]


async def delete_user_setting(
    db: AsyncSession,
    user_id: str,
    category: str,
    key: str,
) -> bool:
    result = await db.execute(
        select(UserSettingsDB).where(
            (UserSettingsDB.user_id == user_id)
            & (UserSettingsDB.category == category)
            & (UserSettingsDB.key == key)
        )
    )
    setting = result.scalar_one_or_none()
    if setting:
        await db.delete(setting)
        await db.commit()
        return True
    return False

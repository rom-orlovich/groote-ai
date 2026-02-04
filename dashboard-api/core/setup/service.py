import json
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.setup.encryption import decrypt_value, encrypt_value
from core.setup.models import SetupConfigDB, SetupStateDB

logger = structlog.get_logger()

SETUP_STEPS = ["welcome", "ai_provider", "github", "jira", "slack", "sentry", "review"]


async def get_setup_state(db: AsyncSession) -> SetupStateDB:
    result = await db.execute(select(SetupStateDB).where(SetupStateDB.id == "singleton"))
    state = result.scalar_one_or_none()
    if not state:
        state = SetupStateDB(id="singleton")
        db.add(state)
        await db.commit()
        await db.refresh(state)
    return state


async def update_setup_step(
    db: AsyncSession,
    step: str,
    action: str,
) -> SetupStateDB:
    state = await get_setup_state(db)
    completed = json.loads(state.completed_steps)
    skipped = json.loads(state.skipped_steps)

    if action == "complete" and step not in completed:
        completed.append(step)
        if step in skipped:
            skipped.remove(step)
    elif action == "skip" and step not in skipped:
        skipped.append(step)
        if step in completed:
            completed.remove(step)

    state.completed_steps = json.dumps(completed)
    state.skipped_steps = json.dumps(skipped)

    total = len(SETUP_STEPS)
    done = len([s for s in SETUP_STEPS if s in completed or s in skipped])
    state.progress_percent = (done / total) * 100 if total > 0 else 0

    step_idx = SETUP_STEPS.index(step) if step in SETUP_STEPS else 0
    if step_idx + 1 < len(SETUP_STEPS):
        state.current_step = SETUP_STEPS[step_idx + 1]

    db.add(state)
    await db.commit()
    await db.refresh(state)
    return state


async def complete_setup(db: AsyncSession) -> SetupStateDB:
    state = await get_setup_state(db)
    state.is_complete = True
    state.completed_at = datetime.now(UTC)
    state.progress_percent = 100.0
    state.current_step = "complete"
    db.add(state)
    await db.commit()
    await db.refresh(state)
    logger.info("setup_completed")
    return state


async def reset_setup(db: AsyncSession) -> SetupStateDB:
    state = await get_setup_state(db)
    state.is_complete = False
    state.completed_at = None
    state.current_step = "welcome"
    state.completed_steps = "[]"
    state.skipped_steps = "[]"
    state.progress_percent = 0.0
    db.add(state)
    await db.commit()
    await db.refresh(state)
    return state


async def save_config(
    db: AsyncSession,
    key: str,
    value: str,
    category: str,
    display_name: str,
    is_sensitive: bool = False,
) -> SetupConfigDB:
    stored_value = encrypt_value(value) if is_sensitive else value
    result = await db.execute(select(SetupConfigDB).where(SetupConfigDB.key == key))
    existing = result.scalar_one_or_none()

    if existing:
        existing.value = stored_value
        existing.category = category
        existing.display_name = display_name
        existing.is_sensitive = is_sensitive
        existing.updated_at = datetime.now(UTC)
        db.add(existing)
    else:
        config = SetupConfigDB(
            key=key,
            value=stored_value,
            category=category,
            display_name=display_name,
            is_sensitive=is_sensitive,
        )
        db.add(config)

    await db.commit()
    return existing or config


async def get_config(db: AsyncSession, key: str) -> str | None:
    result = await db.execute(select(SetupConfigDB).where(SetupConfigDB.key == key))
    config = result.scalar_one_or_none()
    if not config:
        return None
    return decrypt_value(config.value) if config.is_sensitive else config.value


async def get_configs_by_category(
    db: AsyncSession,
    category: str,
) -> list[dict[str, str | bool]]:
    result = await db.execute(
        select(SetupConfigDB).where(SetupConfigDB.category == category)
    )
    configs = result.scalars().all()
    return [
        {
            "key": c.key,
            "value": decrypt_value(c.value) if c.is_sensitive else c.value,
            "display_name": c.display_name,
            "is_sensitive": c.is_sensitive,
        }
        for c in configs
    ]


async def get_all_configs(db: AsyncSession) -> list[dict[str, str | bool]]:
    result = await db.execute(select(SetupConfigDB))
    configs = result.scalars().all()
    return [
        {
            "key": c.key,
            "value": decrypt_value(c.value) if c.is_sensitive else c.value,
            "category": c.category,
            "display_name": c.display_name,
            "is_sensitive": c.is_sensitive,
        }
        for c in configs
    ]


def generate_env_content(configs: list[dict[str, str | bool]]) -> str:
    categories: dict[str, list[dict[str, str | bool]]] = {}
    for c in configs:
        cat = str(c.get("category", "other"))
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(c)

    lines: list[str] = ["# Groote AI Configuration", "# Generated by Setup Wizard", ""]

    category_titles = {
        "infrastructure": "Database Configuration",
        "ai_provider": "AI Provider Configuration",
        "github": "GitHub Configuration",
        "jira": "Jira Configuration",
        "slack": "Slack Configuration",
        "sentry": "Sentry Configuration",
        "webhooks": "Webhook Secrets",
        "general": "General Configuration",
    }

    for cat, items in categories.items():
        title = category_titles.get(cat, cat.replace("_", " ").title())
        lines.append(f"# {'=' * 43}")
        lines.append(f"# {title}")
        lines.append(f"# {'=' * 43}")
        for item in items:
            lines.append(f"{item['key']}={item['value']}")
        lines.append("")

    return "\n".join(lines)

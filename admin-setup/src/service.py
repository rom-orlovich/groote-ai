from datetime import UTC, datetime

from db import AdminSetupConfig, AdminSetupState
from encryption import decrypt_value, encrypt_value
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

STEP_ORDER = ["welcome", "public_url", "github", "jira", "slack", "review"]


async def get_setup_state(db: AsyncSession) -> AdminSetupState:
    result = await db.execute(select(AdminSetupState).limit(1))
    state = result.scalar_one_or_none()
    if not state:
        state = AdminSetupState(id="admin")
        db.add(state)
        await db.commit()
        await db.refresh(state)
    return state


async def update_setup_step(db: AsyncSession, step_id: str, skip: bool = False) -> AdminSetupState:
    state = await get_setup_state(db)
    completed = state.get_completed_steps()
    skipped = state.get_skipped_steps()

    if skip and step_id not in skipped:
        skipped.append(step_id)
    elif step_id not in completed:
        completed.append(step_id)

    state.set_completed_steps(completed)
    state.set_skipped_steps(skipped)

    current_idx = STEP_ORDER.index(step_id) if step_id in STEP_ORDER else 0
    if current_idx + 1 < len(STEP_ORDER):
        state.current_step = STEP_ORDER[current_idx + 1]

    total = len(STEP_ORDER)
    done = len(set(completed) | set(skipped))
    state.progress_percent = (done / total) * 100

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
) -> AdminSetupConfig:
    stored_value = encrypt_value(value) if is_sensitive else value

    result = await db.execute(
        select(AdminSetupConfig).where(
            AdminSetupConfig.key == key, AdminSetupConfig.scope == "admin"
        )
    )
    config = result.scalar_one_or_none()

    if config:
        config.value = stored_value
        config.category = category
        config.display_name = display_name
        config.is_sensitive = is_sensitive
        config.updated_at = datetime.now(UTC)
    else:
        config = AdminSetupConfig(
            key=key,
            value=stored_value,
            category=category,
            display_name=display_name,
            is_sensitive=is_sensitive,
            scope="admin",
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)
    return config


async def get_config(db: AsyncSession, key: str) -> str | None:
    result = await db.execute(
        select(AdminSetupConfig).where(
            AdminSetupConfig.key == key, AdminSetupConfig.scope == "admin"
        )
    )
    config = result.scalar_one_or_none()
    if not config:
        return None
    return decrypt_value(config.value) if config.is_sensitive else config.value


async def get_configs_by_category(db: AsyncSession, category: str) -> dict[str, str]:
    result = await db.execute(
        select(AdminSetupConfig).where(
            AdminSetupConfig.category == category,
            AdminSetupConfig.scope == "admin",
        )
    )
    configs = result.scalars().all()
    output: dict[str, str] = {}
    for c in configs:
        output[c.key] = decrypt_value(c.value) if c.is_sensitive else c.value
    return output


async def get_all_configs(db: AsyncSession) -> list[AdminSetupConfig]:
    result = await db.execute(select(AdminSetupConfig).where(AdminSetupConfig.scope == "admin"))
    return list(result.scalars().all())


SENSITIVE_KEYS = {
    "GITHUB_CLIENT_SECRET",
    "GITHUB_WEBHOOK_SECRET",
    "JIRA_CLIENT_SECRET",
    "SLACK_CLIENT_SECRET",
    "SLACK_SIGNING_SECRET",
    "SLACK_STATE_SECRET",
}


async def get_masked_configs(db: AsyncSession) -> list[dict[str, str | bool]]:
    configs = await get_all_configs(db)
    result: list[dict[str, str | bool]] = []
    for config in configs:
        value = decrypt_value(config.value) if config.is_sensitive else config.value
        is_masked = config.key in SENSITIVE_KEYS
        if is_masked and value and len(value) > 3:
            value = "\u2022\u2022\u2022\u2022\u2022\u2022" + value[-3:]
        elif is_masked and value:
            value = "\u2022\u2022\u2022\u2022\u2022\u2022"
        result.append({
            "key": config.key,
            "value": value or "",
            "category": config.category,
            "is_masked": is_masked,
        })
    return result


def generate_env_content(configs: list[AdminSetupConfig]) -> str:
    lines: list[str] = []
    current_category = ""
    has_private_key_file = False
    for config in sorted(configs, key=lambda c: c.category):
        if config.category != current_category:
            if current_category:
                lines.append("")
            current_category = config.category
        value = decrypt_value(config.value) if config.is_sensitive else config.value
        lines.append(f"{config.key}={value}")
        if config.key == "GITHUB_PRIVATE_KEY_FILE":
            has_private_key_file = True
    if has_private_key_file:
        lines.append("")
        lines.append("GITHUB_PRIVATE_KEY_PATH=/secrets/github-private-key.pem")
    return "\n".join(lines) + "\n"


async def complete_setup(db: AsyncSession) -> AdminSetupState:
    state = await get_setup_state(db)
    state.is_complete = True
    state.progress_percent = 100
    state.completed_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(state)
    return state


async def reset_setup(db: AsyncSession) -> AdminSetupState:
    state = await get_setup_state(db)
    state.is_complete = False
    state.current_step = "welcome"
    state.set_completed_steps([])
    state.set_skipped_steps([])
    state.progress_percent = 0
    state.completed_at = None

    result = await db.execute(select(AdminSetupConfig).where(AdminSetupConfig.scope == "admin"))
    for config in result.scalars().all():
        await db.delete(config)

    await db.commit()
    await db.refresh(state)
    return state

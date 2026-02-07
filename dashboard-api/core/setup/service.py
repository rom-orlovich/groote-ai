import json
from datetime import UTC, datetime

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.setup.encryption import decrypt_value, encrypt_value
from core.setup.models import SetupConfigDB, SetupStateDB

logger = structlog.get_logger()

SETUP_STEPS = [
    "welcome",
    "ai_provider",
    "github_oauth",
    "jira_oauth",
    "slack_oauth",
    "sentry",
    "review",
]


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
    if not config or config.value is None:
        return None
    return decrypt_value(config.value) if config.is_sensitive else config.value


async def get_configs_by_category(
    db: AsyncSession,
    category: str,
) -> list[dict[str, str | bool]]:
    result = await db.execute(select(SetupConfigDB).where(SetupConfigDB.category == category))
    configs = result.scalars().all()
    return [
        {
            "key": c.key,
            "value": decrypt_value(c.value) if c.is_sensitive and c.value else c.value,
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
            "value": decrypt_value(c.value) if c.is_sensitive and c.value else c.value,
            "category": c.category,
            "display_name": c.display_name,
            "is_sensitive": c.is_sensitive,
        }
        for c in configs
    ]


CATEGORY_TITLES = {
    "infrastructure": "Database Configuration",
    "ai_provider": "AI Provider Configuration",
    "github_oauth": "GitHub Configuration",
    "jira_oauth": "Jira Configuration",
    "slack_oauth": "Slack Configuration",
    "sentry": "Sentry Configuration",
    "webhooks": "Webhook Secrets",
    "general": "General Configuration",
}


def _group_by_category(
    configs: list[dict[str, str | bool]],
) -> dict[str, list[dict[str, str | bool]]]:
    categories: dict[str, list[dict[str, str | bool]]] = {}
    for c in configs:
        cat = str(c.get("category", "other"))
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(c)
    return categories


def _needs_quoting(value: str) -> bool:
    return "\n" in value or '"' in value or "'" in value or " " in value or "=" in value


def generate_env_content(configs: list[dict[str, str | bool]]) -> str:
    from core.setup.encryption import get_encryption_key

    categories = _group_by_category(configs)
    lines: list[str] = ["# Groote AI Configuration", "# Generated by Setup Wizard", ""]

    lines.append(f"# {'=' * 43}")
    lines.append("# Encryption")
    lines.append(f"# {'=' * 43}")
    lines.append(f"TOKEN_ENCRYPTION_KEY={get_encryption_key()}")
    lines.append("")

    for cat, items in categories.items():
        title = CATEGORY_TITLES.get(cat, cat.replace("_", " ").title())
        lines.append(f"# {'=' * 43}")
        lines.append(f"# {title}")
        lines.append(f"# {'=' * 43}")
        for item in items:
            val = str(item["value"])
            if _needs_quoting(val):
                lines.append(f'{item["key"]}="{val}"')
            else:
                lines.append(f"{item['key']}={val}")
        lines.append("")

    return "\n".join(lines)


def generate_k8s_secret(configs: list[dict[str, str | bool]], namespace: str = "default") -> str:
    import base64

    lines = [
        "apiVersion: v1",
        "kind: Secret",
        "metadata:",
        "  name: groote-ai-config",
        f"  namespace: {namespace}",
        "type: Opaque",
        "data:",
    ]
    for c in configs:
        val = base64.b64encode(str(c["value"]).encode()).decode()
        lines.append(f"  {c['key']}: {val}")
    return "\n".join(lines)


def generate_docker_secrets_script(configs: list[dict[str, str | bool]]) -> str:
    lines = [
        "#!/bin/bash",
        "# Groote AI - Docker Secrets creation script",
        "# Run in Docker Swarm mode: docker swarm init",
        "",
    ]
    for c in configs:
        key = str(c["key"]).lower()
        val = str(c["value"])
        if "\n" in val:
            lines.append(f"cat <<'GROOTE_EOF' | docker secret create groote_{key} -")
            lines.append(val)
            lines.append("GROOTE_EOF")
        else:
            lines.append(f"echo -n '{val}' | docker secret create groote_{key} -")
    return "\n".join(lines)


def generate_github_actions_env(configs: list[dict[str, str | bool]]) -> str:
    lines = [
        "# GitHub Actions - add these as Repository Secrets",
        "# Settings > Secrets and variables > Actions > New repository secret",
        "",
    ]
    for c in configs:
        is_sensitive = c.get("is_sensitive", False)
        if is_sensitive:
            lines.append(f"# Secret: {c['key']} = <set in GitHub UI>")
        else:
            lines.append(f"# Variable: {c['key']} = {c['value']}")
    return "\n".join(lines)

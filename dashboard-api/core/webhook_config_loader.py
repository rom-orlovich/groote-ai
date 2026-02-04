from pathlib import Path

import structlog
from shared.machine_models import WebhookConfig, WebhookYamlConfig

logger = structlog.get_logger()

WEBHOOK_CONFIG_DIR = Path(__file__).parent.parent / "api" / "webhooks"


def load_webhook_config(name: str) -> WebhookConfig | None:
    config_path = WEBHOOK_CONFIG_DIR / name / "config.yaml"
    if not config_path.exists():
        return None
    try:
        yaml_config = WebhookYamlConfig.from_yaml_file(config_path)
        return yaml_config.to_webhook_config()
    except Exception as e:
        logger.error("webhook_config_load_failed", name=name, error=str(e))
        return None


def load_all_webhook_configs() -> list[WebhookConfig]:
    configs: list[WebhookConfig] = []
    if not WEBHOOK_CONFIG_DIR.exists():
        logger.warning("webhook_config_dir_missing", path=str(WEBHOOK_CONFIG_DIR))
        return configs

    for config_dir in sorted(WEBHOOK_CONFIG_DIR.iterdir()):
        if not config_dir.is_dir():
            continue
        config = load_webhook_config(config_dir.name)
        if config:
            configs.append(config)

    logger.info("webhook_configs_loaded", count=len(configs))
    return configs


def validate_all_configs() -> bool:
    configs = load_all_webhook_configs()
    for config in configs:
        if not config.name or not config.endpoint:
            logger.error("webhook_config_invalid", name=config.name)
            return False
    return True


def get_agent_trigger_info(webhook_name: str) -> dict | None:
    config_path = WEBHOOK_CONFIG_DIR / webhook_name / "config.yaml"
    if not config_path.exists():
        return None
    try:
        yaml_config = WebhookYamlConfig.from_yaml_file(config_path)
        trigger = yaml_config.agent_trigger
        return {
            "prefix": trigger.prefix,
            "aliases": trigger.aliases,
            "assignee_trigger": trigger.assignee_trigger,
        }
    except Exception as e:
        logger.error("agent_trigger_info_failed", name=webhook_name, error=str(e))
        return None

import os

from pydantic import BaseModel, ConfigDict


class AuditConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    api_gateway_url: str = "http://localhost:8000"
    dashboard_api_url: str = "http://localhost:5000"
    task_logger_url: str = "http://localhost:8090"
    llamaindex_url: str = "http://localhost:8002"
    gkg_url: str = "http://localhost:8003"
    redis_url: str = "redis://localhost:6379/0"
    github_api_url: str = "http://localhost:3001"
    jira_api_url: str = "http://localhost:3002"
    slack_api_url: str = "http://localhost:3003"

    github_owner: str = "rom-orlovich"
    github_repo: str = "manga-creator"
    jira_project: str = "AUDIT"
    slack_channel: str

    timeout_webhook: float = 15.0
    timeout_task_created: float = 20.0
    timeout_task_pickup: float = 30.0
    timeout_context: float = 15.0
    timeout_execution: float = 300.0
    timeout_response: float = 30.0
    timeout_multiplier: float = 1.0

    quality_pass_threshold: int = 70

    output_dir: str = "./audit-results"
    cleanup: bool = False
    verbose: bool = False

    def scaled_timeout(self, base: float) -> float:
        return base * self.timeout_multiplier


def load_config() -> AuditConfig:
    return AuditConfig(
        api_gateway_url=os.getenv("AUDIT_API_GATEWAY_URL", "http://localhost:8000"),
        dashboard_api_url=os.getenv("AUDIT_DASHBOARD_API_URL", "http://localhost:5000"),
        task_logger_url=os.getenv("AUDIT_TASK_LOGGER_URL", "http://localhost:8090"),
        llamaindex_url=os.getenv("AUDIT_LLAMAINDEX_URL", "http://localhost:8002"),
        gkg_url=os.getenv("AUDIT_GKG_URL", "http://localhost:8003"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        github_api_url=os.getenv("AUDIT_GITHUB_API_URL", "http://localhost:3001"),
        jira_api_url=os.getenv("AUDIT_JIRA_API_URL", "http://localhost:3002"),
        slack_api_url=os.getenv("AUDIT_SLACK_API_URL", "http://localhost:3003"),
        github_owner=os.getenv("AUDIT_GITHUB_OWNER", "rom-orlovich"),
        github_repo=os.getenv("AUDIT_GITHUB_REPO", "manga-creator"),
        jira_project=os.getenv("AUDIT_JIRA_PROJECT", "AUDIT"),
        slack_channel=os.getenv("AUDIT_SLACK_CHANNEL", "C_audit_test"),
        timeout_webhook=float(os.getenv("AUDIT_TIMEOUT_WEBHOOK", "15.0")),
        timeout_task_created=float(os.getenv("AUDIT_TIMEOUT_TASK_CREATED", "20.0")),
        timeout_task_pickup=float(os.getenv("AUDIT_TIMEOUT_TASK_PICKUP", "30.0")),
        timeout_context=float(os.getenv("AUDIT_TIMEOUT_CONTEXT", "15.0")),
        timeout_execution=float(os.getenv("AUDIT_TIMEOUT_EXECUTION", "300.0")),
        timeout_response=float(os.getenv("AUDIT_TIMEOUT_RESPONSE", "30.0")),
        timeout_multiplier=float(os.getenv("AUDIT_TIMEOUT_MULTIPLIER", "1.0")),
        quality_pass_threshold=int(os.getenv("AUDIT_QUALITY_THRESHOLD", "70")),
        output_dir=os.getenv("AUDIT_OUTPUT_DIR", "./audit-results"),
        cleanup=os.getenv("AUDIT_CLEANUP", "false").lower() == "true",
        verbose=os.getenv("AUDIT_VERBOSE", "false").lower() == "true",
    )

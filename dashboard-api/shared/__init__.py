"""Shared models and utilities."""

from .machine_models import (
    AgentType,
    APIResponse,
    AuthStatus,
    ChatMessage,
    ClaudeCredentials,
    CreateAgentRequest,
    # Request/Response
    CreateWebhookRequest,
    EntityType,
    # Core Models
    MachineConfig,
    Session,
    SkillConfig,
    SubAgentConfig,
    Task,
    TaskCompletedMessage,
    TaskCreatedMessage,
    TaskFailedMessage,
    TaskMetricsMessage,
    TaskOutputMessage,
    # Enums
    TaskStatus,
    TaskStatusMessage,
    TaskStopMessage,
    UploadCredentialsRequest,
    UserInputMessage,
    WebhookCommand,
    WebhookConfig,
    # WebSocket Messages
    WebSocketMessage,
    WSMessage,
)

__all__ = [
    "APIResponse",
    "AgentType",
    "AuthStatus",
    "ChatMessage",
    "ClaudeCredentials",
    "CreateAgentRequest",
    # Request/Response
    "CreateWebhookRequest",
    "EntityType",
    # Core Models
    "MachineConfig",
    "Session",
    "SkillConfig",
    "SubAgentConfig",
    "Task",
    "TaskCompletedMessage",
    "TaskCreatedMessage",
    "TaskFailedMessage",
    "TaskMetricsMessage",
    "TaskOutputMessage",
    # Enums
    "TaskStatus",
    "TaskStatusMessage",
    "TaskStopMessage",
    "UploadCredentialsRequest",
    "UserInputMessage",
    "WSMessage",
    # WebSocket Messages
    "WebSocketMessage",
    "WebhookCommand",
    "WebhookConfig",
]

from pydantic import BaseModel, ConfigDict


class AIProviderSettings(BaseModel):
    model_config = ConfigDict(strict=True)

    provider: str
    api_key: str | None = None
    model_complex: str | None = None
    model_execution: str | None = None


class AgentScalingSettings(BaseModel):
    model_config = ConfigDict(strict=True)

    agent_count: int
    max_agents: int = 20
    min_agents: int = 1


class UserSettingsResponse(BaseModel):
    model_config = ConfigDict(strict=True)

    user_id: str
    category: str
    key: str
    value: str

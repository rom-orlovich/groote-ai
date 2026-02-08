from pydantic import BaseModel, ConfigDict


class SetupStep(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    title: str
    description: str
    status: str


class SetupStatus(BaseModel):
    model_config = ConfigDict(strict=True)

    is_authenticated: bool
    steps: list[SetupStep]
    progress: int


class OAuthAppConfig(BaseModel):
    model_config = ConfigDict(strict=True)

    platform: str
    client_id: str
    client_secret: str
    private_key: str | None = None
    webhook_secret: str | None = None


class AdminSetupComplete(BaseModel):
    model_config = ConfigDict(strict=True)

    status: str
    message: str

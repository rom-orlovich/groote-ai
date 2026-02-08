from pydantic import BaseModel, ConfigDict


class AuthRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    token: str


class AuthResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    authenticated: bool


class SetupStatusResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    is_complete: bool
    current_step: str
    completed_steps: list[str]
    skipped_steps: list[str]
    progress_percent: int


class ServiceHealth(BaseModel):
    model_config = ConfigDict(strict=True)
    healthy: bool
    message: str


class InfrastructureResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    postgres: ServiceHealth
    redis: ServiceHealth


class SaveStepRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    configs: dict[str, str] = {}
    skip: bool = False


class SaveStepResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    success: bool
    current_step: str
    progress_percent: int


class ValidateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    configs: dict[str, str]


class ValidateResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    valid: bool
    message: str


class ExportResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str
    filename: str


class CompleteResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    status: str
    message: str

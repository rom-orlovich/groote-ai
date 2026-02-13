from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TriggerResult(BaseModel):
    model_config = ConfigDict(strict=True)

    platform: str
    artifact_type: str
    artifact_id: str
    artifact_url: str | None = None
    trigger_time: datetime
    expected_flow_id: str
    raw_response: dict = {}

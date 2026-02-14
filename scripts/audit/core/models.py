from pydantic import BaseModel, ConfigDict


class QualityDimension(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    score: int
    detail: str


class QualityReport(BaseModel):
    model_config = ConfigDict(strict=True)

    task_id: str
    dimensions: list[QualityDimension]
    overall_score: int
    passed: bool
    suggestions: list[str]


class FlowCriteria(BaseModel):
    model_config = ConfigDict(strict=True)

    expected_agent: str
    required_tools: list[str] = []
    required_response_tools: list[str] = []
    required_output_patterns: list[str] = []
    negative_output_patterns: list[str] = []
    domain_terms: list[str] = []
    negative_terms: list[str] = []
    target_repo: str = ""
    min_output_length: int = 100
    max_execution_seconds: float = 300.0
    requires_knowledge: bool = True

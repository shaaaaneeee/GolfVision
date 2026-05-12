from pydantic import BaseModel, Field


class AnalysisJob(BaseModel):
    job_id: str


class FaultResult(BaseModel):
    name: str
    severity: float = Field(ge=0.0, le=1.0)
    display_name: str


class AnalysisResult(BaseModel):
    job_id: str
    status: str  # "queued" | "processing" | "complete" | "failed"
    faults: list[FaultResult] | None = None
    coaching: str | None = None
    features: dict[str, float] | None = None
    error: str | None = None

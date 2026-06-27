from datetime import date

from pydantic import BaseModel, Field


class AIParseTaskRequest(BaseModel):
    raw_text: str = Field(min_length=3)
    created_by: str | None = None


class AIParsedTaskPayload(BaseModel):
    task_title: str
    goal: str | None = None
    task_type_id: int | None = None
    business_area: str | None = None
    customer: str | None = None
    priority_id: int | None = None
    complexity_id: int | None = None
    executor: str | None = None
    planned_finish_date: date | None = None
    source_text: str
    ai_confidence: float | None = None
    created_by: str | None = None
    parser_notes: list[str] = Field(default_factory=list)
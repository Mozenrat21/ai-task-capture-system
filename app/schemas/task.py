from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TaskListResponse(BaseModel):
    id: int
    task_title: str
    goal: str | None = None
    auto_status: str
    business_area: str | None = None
    customer: str | None = None
    executor: str | None = None
    planned_finish_date: date | None = None
    fact_start_date: date | None = None
    fact_finish_date: date | None = None
    fact_hours: Decimal | None = None
    auto_task_score: Decimal | None = None
    short_status_description: str | None = None
    created_at: datetime
    updated_at: datetime

    task_type_name: str | None = None
    priority_name: str | None = None
    complexity_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class TaskDetailResponse(TaskListResponse):
    task_type_id: int | None = None
    priority_id: int | None = None
    complexity_id: int | None = None
    extra_column: str | None = None
    plan_fact: str | None = None
    source_text: str | None = None
    ai_confidence: Decimal | None = None
    created_by: str | None = None
    is_deleted: bool
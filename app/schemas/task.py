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

class TaskCreatePreviewRequest(BaseModel):
    task_title: str
    goal: str | None = None
    task_type_id: int | None = None
    business_area: str | None = None
    customer: str | None = None
    priority_id: int | None = None
    complexity_id: int | None = None
    executor: str | None = None
    planned_finish_date: date | None = None
    fact_start_date: date | None = None
    fact_finish_date: date | None = None
    fact_hours: Decimal | None = None
    short_status_description: str | None = None
    source_text: str | None = None
    ai_confidence: Decimal | None = None
    created_by: str | None = None


class ProposedChangeResponse(BaseModel):
    field: str
    old_value: str | int | float | bool | None = None
    new_value: str | int | float | bool | None = None


class TaskPreviewResponse(BaseModel):
    preview_id: int
    action: str
    target_task_id: int | None = None
    proposed_changes: list[ProposedChangeResponse]
    warnings: list[str]
    can_confirm: bool


class ConfirmPreviewRequest(BaseModel):
    preview_id: int


class ConfirmPreviewResponse(BaseModel):
    status: str
    task_id: int
    message: str

class TaskClosePreviewRequest(BaseModel):
    fact_finish_date: date | None = None
    fact_hours: Decimal | None = None
    short_status_description: str | None = None
    source_text: str | None = None
    created_by: str | None = None

class TaskStartPreviewRequest(BaseModel):
    fact_start_date: date | None = None
    source_text: str | None = None
    created_by: str | None = None

class TaskPlanPreviewRequest(BaseModel):
    fact_start_date: date
    planned_finish_date: date | None = None
    source_text: str | None = None
    created_by: str | None = None

class TaskPausePreviewRequest(BaseModel):
    pause_reason: str | None = None
    source_text: str | None = None
    created_by: str | None = None

class TaskResumePreviewRequest(BaseModel):
    resume_note: str | None = None
    source_text: str | None = None
    created_by: str | None = None

class TaskUpdatePreviewRequest(BaseModel):
    task_title: str | None = None
    goal: str | None = None
    task_type_id: int | None = None
    business_area: str | None = None
    customer: str | None = None
    priority_id: int | None = None
    complexity_id: int | None = None
    executor: str | None = None
    extra_column: str | None = None
    plan_fact: str | None = None
    planned_finish_date: date | None = None
    short_status_description: str | None = None
    source_text: str | None = None
    created_by: str | None = None
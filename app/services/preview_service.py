from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dictionaries import ComplexityDict, PriorityDict, TaskTypeDict
from app.models.task import Task
from app.models.task_preview import TaskPreview
from app.schemas.task import TaskCreatePreviewRequest
from app.services.event_service import create_task_event
from app.services.score_service import calculate_auto_task_score
from app.services.status_service import calculate_auto_status


PREVIEW_STATUS_PENDING = "pending"
PREVIEW_STATUS_CONFIRMED = "confirmed"
PREVIEW_STATUS_EXPIRED = "expired"

ACTION_CREATE_TASK = "create_task"


DATE_FIELDS = {
    "planned_finish_date",
    "fact_start_date",
    "fact_finish_date",
}

DECIMAL_FIELDS = {
    "auto_task_score",
    "fact_hours",
    "ai_confidence",
}


def serialize_value(value):
    """
    Converts Python values to JSONB-safe values.

    PostgreSQL JSONB does not accept date/datetime/Decimal directly.
    """

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return str(value)

    return value


def deserialize_task_data(task_data: dict) -> dict:
    """
    Converts JSONB-safe values back to Python values for SQLAlchemy models.
    """

    result = dict(task_data)

    for field in DATE_FIELDS:
        value = result.get(field)

        if isinstance(value, str):
            result[field] = date.fromisoformat(value)

    for field in DECIMAL_FIELDS:
        value = result.get(field)

        if value is not None and not isinstance(value, Decimal):
            result[field] = Decimal(str(value))

    return result


def build_proposed_changes(data: dict) -> list[dict]:
    """
    Builds list of proposed changes for preview response.
    For create action old_value is always None.
    """

    changes = []

    for field, value in data.items():
        if value is not None:
            changes.append(
                {
                    "field": field,
                    "old_value": None,
                    "new_value": serialize_value(value),
                }
            )

    return changes


def get_task_type(db: Session, task_type_id: int | None) -> TaskTypeDict | None:
    if task_type_id is None:
        return None

    return db.scalar(
        select(TaskTypeDict).where(
            TaskTypeDict.id == task_type_id,
            TaskTypeDict.is_active.is_(True),
        )
    )


def get_priority(db: Session, priority_id: int | None) -> PriorityDict | None:
    if priority_id is None:
        return None

    return db.scalar(
        select(PriorityDict).where(
            PriorityDict.id == priority_id,
            PriorityDict.is_active.is_(True),
        )
    )


def get_complexity(db: Session, complexity_id: int | None) -> ComplexityDict | None:
    if complexity_id is None:
        return None

    return db.scalar(
        select(ComplexityDict).where(
            ComplexityDict.id == complexity_id,
            ComplexityDict.is_active.is_(True),
        )
    )


def create_task_preview(
    db: Session,
    request: TaskCreatePreviewRequest,
) -> TaskPreview:
    """
    Creates preview for new task.

    Important:
    this function does not write a task to tasks table.
    It only prepares proposed changes for user confirmation.
    """

    task_type = get_task_type(db, request.task_type_id)
    priority = get_priority(db, request.priority_id)
    complexity = get_complexity(db, request.complexity_id)

    warnings = []

    if request.task_type_id is not None and task_type is None:
        warnings.append(f"Task type id={request.task_type_id} not found or inactive.")

    if request.priority_id is not None and priority is None:
        warnings.append(f"Priority id={request.priority_id} not found or inactive.")

    if request.complexity_id is not None and complexity is None:
        warnings.append(f"Complexity id={request.complexity_id} not found or inactive.")

    auto_status = calculate_auto_status(
        priority_id=request.priority_id if priority else None,
        complexity_id=request.complexity_id if complexity else None,
        fact_start_date=request.fact_start_date,
        fact_finish_date=request.fact_finish_date,
    )

    auto_task_score = calculate_auto_task_score(
        task_type_base_hours=task_type.base_hours if task_type else None,
        priority_coefficient=priority.coefficient if priority else None,
        complexity_coefficient=complexity.coefficient if complexity else None,
    )

    task_data = request.model_dump()
    task_data["auto_status"] = auto_status
    task_data["auto_task_score"] = auto_task_score

    proposed_changes = build_proposed_changes(task_data)

    preview = TaskPreview(
        action=ACTION_CREATE_TASK,
        raw_text=request.source_text,
        ai_payload=None,
        resolved_changes={
            "task_data": {
                key: serialize_value(value)
                for key, value in task_data.items()
            },
            "proposed_changes": proposed_changes,
        },
        warnings=warnings,
        status=PREVIEW_STATUS_PENDING,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        created_by=request.created_by,
    )

    db.add(preview)
    db.commit()
    db.refresh(preview)

    return preview


def confirm_task_preview(
    db: Session,
    preview_id: int,
) -> Task:
    """
    Confirms pending preview and writes task to database.
    """

    preview = db.get(TaskPreview, preview_id)

    if preview is None:
        raise HTTPException(status_code=404, detail="Preview not found")

    if preview.status != PREVIEW_STATUS_PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Preview is not pending. Current status: {preview.status}",
        )

    if preview.expires_at is not None and preview.expires_at < datetime.now(UTC):
        preview.status = PREVIEW_STATUS_EXPIRED
        db.commit()

        raise HTTPException(status_code=400, detail="Preview expired")

    if preview.action != ACTION_CREATE_TASK:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported preview action: {preview.action}",
        )

    if not preview.resolved_changes or "task_data" not in preview.resolved_changes:
        raise HTTPException(
            status_code=400,
            detail="Preview does not contain task data.",
        )

    task_data = deserialize_task_data(preview.resolved_changes["task_data"])

    task = Task(
        task_title=task_data["task_title"],
        goal=task_data.get("goal"),
        task_type_id=task_data.get("task_type_id"),
        business_area=task_data.get("business_area"),
        customer=task_data.get("customer"),
        auto_status=task_data["auto_status"],
        priority_id=task_data.get("priority_id"),
        complexity_id=task_data.get("complexity_id"),
        auto_task_score=task_data.get("auto_task_score"),
        executor=task_data.get("executor"),
        planned_finish_date=task_data.get("planned_finish_date"),
        fact_start_date=task_data.get("fact_start_date"),
        fact_finish_date=task_data.get("fact_finish_date"),
        fact_hours=task_data.get("fact_hours"),
        short_status_description=task_data.get("short_status_description"),
        source_text=task_data.get("source_text"),
        ai_confidence=task_data.get("ai_confidence"),
        created_by=task_data.get("created_by"),
    )

    db.add(task)
    db.flush()

    create_task_event(
        db=db,
        task_id=task.id,
        event_type="created",
        field_name=None,
        old_value=None,
        new_value={"task_title": task.task_title},
        comment="Task created from confirmed preview.",
        created_by=task.created_by,
        source="preview",
    )

    preview.status = PREVIEW_STATUS_CONFIRMED
    preview.confirmed_at = datetime.now(UTC)
    preview.target_task_id = task.id

    db.commit()
    db.refresh(task)

    return task
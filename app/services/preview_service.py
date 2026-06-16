from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dictionaries import ComplexityDict, PriorityDict, TaskTypeDict
from app.models.task import Task
from app.models.task_preview import TaskPreview
from app.schemas.task import (
    TaskClosePreviewRequest,
    TaskCreatePreviewRequest,
    TaskPlanPreviewRequest,
    TaskStartPreviewRequest,
    TaskPausePreviewRequest,
    TaskResumePreviewRequest,
)
from app.services.event_service import create_task_event
from app.services.score_service import calculate_auto_task_score
from app.services.status_service import calculate_auto_status


PREVIEW_STATUS_PENDING = "pending"
PREVIEW_STATUS_CONFIRMED = "confirmed"
PREVIEW_STATUS_EXPIRED = "expired"

ACTION_CREATE_TASK = "create_task"
ACTION_CLOSE_TASK = "close_task"
ACTION_START_TASK = "start_task"
ACTION_PLAN_TASK = "plan_task"
ACTION_PAUSE_TASK = "pause_task"
ACTION_RESUME_TASK = "resume_task"

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


def build_create_proposed_changes(data: dict) -> list[dict]:
    """
    Builds proposed changes for create preview.
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


def build_update_proposed_changes(old_data: dict, new_data: dict) -> list[dict]:
    """
    Builds proposed changes for update-like preview.
    """

    changes = []

    for field, new_value in new_data.items():
        old_value = old_data.get(field)

        if serialize_value(old_value) != serialize_value(new_value):
            changes.append(
                {
                    "field": field,
                    "old_value": serialize_value(old_value),
                    "new_value": serialize_value(new_value),
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

    proposed_changes = build_create_proposed_changes(task_data)

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


def create_close_task_preview(
    db: Session,
    task_id: int,
    request: TaskClosePreviewRequest,
) -> TaskPreview:
    """
    Creates preview for closing an existing task.

    Important:
    this function does not update task immediately.
    """

    task = db.get(Task, task_id)

    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    warnings = []

    if task.fact_finish_date is not None:
        warnings.append("Task is already closed.")

    fact_finish_date = request.fact_finish_date or date.today()

    new_values = {
        "fact_finish_date": fact_finish_date,
        "auto_status": calculate_auto_status(
            priority_id=task.priority_id,
            complexity_id=task.complexity_id,
            fact_start_date=task.fact_start_date,
            fact_finish_date=fact_finish_date,
        ),
    }

    if request.fact_hours is not None:
        new_values["fact_hours"] = request.fact_hours

    if request.short_status_description is not None:
        new_values["short_status_description"] = request.short_status_description

    old_values = {
        "fact_finish_date": task.fact_finish_date,
        "auto_status": task.auto_status,
        "fact_hours": task.fact_hours,
        "short_status_description": task.short_status_description,
    }

    proposed_changes = build_update_proposed_changes(
        old_data=old_values,
        new_data=new_values,
    )

    preview = TaskPreview(
        action=ACTION_CLOSE_TASK,
        raw_text=request.source_text,
        ai_payload=None,
        resolved_changes={
            "task_id": task.id,
            "task_data": {
                key: serialize_value(value)
                for key, value in new_values.items()
            },
            "proposed_changes": proposed_changes,
        },
        warnings=warnings,
        target_task_id=task.id,
        status=PREVIEW_STATUS_PENDING,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        created_by=request.created_by,
    )

    db.add(preview)
    db.commit()
    db.refresh(preview)

    return preview

def create_start_task_preview(
    db: Session,
    task_id: int,
    request: TaskStartPreviewRequest,
) -> TaskPreview:
    """
    Creates preview for starting an existing task.

    Important:
    this function does not update task immediately.
    It only prepares proposed changes for user confirmation.
    """

    task = db.get(Task, task_id)

    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    warnings = []

    if task.fact_finish_date is not None:
        warnings.append("Task is already closed.")

    if task.fact_start_date is not None:
        warnings.append("Task already has fact start date.")

    fact_start_date = request.fact_start_date or date.today()

    new_values = {
        "fact_start_date": fact_start_date,
        "auto_status": calculate_auto_status(
            priority_id=task.priority_id,
            complexity_id=task.complexity_id,
            fact_start_date=fact_start_date,
            fact_finish_date=task.fact_finish_date,
        ),
    }

    old_values = {
        "fact_start_date": task.fact_start_date,
        "auto_status": task.auto_status,
    }

    proposed_changes = build_update_proposed_changes(
        old_data=old_values,
        new_data=new_values,
    )

    preview = TaskPreview(
        action=ACTION_START_TASK,
        raw_text=request.source_text,
        ai_payload=None,
        resolved_changes={
            "task_id": task.id,
            "task_data": {
                key: serialize_value(value)
                for key, value in new_values.items()
            },
            "proposed_changes": proposed_changes,
        },
        warnings=warnings,
        target_task_id=task.id,
        status=PREVIEW_STATUS_PENDING,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        created_by=request.created_by,
    )

    db.add(preview)
    db.commit()
    db.refresh(preview)

    return preview

def create_plan_task_preview(
    db: Session,
    task_id: int,
    request: TaskPlanPreviewRequest,
) -> TaskPreview:
    """
    Creates preview for planning an existing task.

    Important:
    this function does not update task immediately.
    It only prepares proposed changes for user confirmation.
    """

    task = db.get(Task, task_id)

    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    warnings = []

    if task.fact_finish_date is not None:
        warnings.append("Task is already closed.")

    if request.fact_start_date <= date.today():
        warnings.append("Plan start date must be in the future to set status План.")

    new_values = {
        "fact_start_date": request.fact_start_date,
        "auto_status": calculate_auto_status(
            priority_id=task.priority_id,
            complexity_id=task.complexity_id,
            fact_start_date=request.fact_start_date,
            fact_finish_date=task.fact_finish_date,
        ),
    }

    if request.planned_finish_date is not None:
        new_values["planned_finish_date"] = request.planned_finish_date

    old_values = {
        "fact_start_date": task.fact_start_date,
        "planned_finish_date": task.planned_finish_date,
        "auto_status": task.auto_status,
    }

    proposed_changes = build_update_proposed_changes(
        old_data=old_values,
        new_data=new_values,
    )

    preview = TaskPreview(
        action=ACTION_PLAN_TASK,
        raw_text=request.source_text,
        ai_payload=None,
        resolved_changes={
            "task_id": task.id,
            "task_data": {
                key: serialize_value(value)
                for key, value in new_values.items()
            },
            "proposed_changes": proposed_changes,
        },
        warnings=warnings,
        target_task_id=task.id,
        status=PREVIEW_STATUS_PENDING,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        created_by=request.created_by,
    )

    db.add(preview)
    db.commit()
    db.refresh(preview)

    return preview

def create_pause_task_preview(
    db: Session,
    task_id: int,
    request: TaskPausePreviewRequest,
) -> TaskPreview:
    """
    Creates preview for pausing an existing task.

    This function does not update task immediately.
    It only prepares proposed changes for user confirmation.
    """

    task = db.get(Task, task_id)

    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    warnings = []

    if task.fact_finish_date is not None:
        warnings.append("Task is already closed.")

    if task.fact_start_date is None:
        warnings.append("Task has not been started yet.")

    if task.auto_status == "Пауза":
        warnings.append("Task is already paused.")

    pause_description = request.pause_reason or "Поставлено на паузу."

    new_values = {
        "auto_status": "Пауза",
        "short_status_description": pause_description,
    }

    old_values = {
        "auto_status": task.auto_status,
        "short_status_description": task.short_status_description,
    }

    proposed_changes = build_update_proposed_changes(
        old_data=old_values,
        new_data=new_values,
    )

    preview = TaskPreview(
        action=ACTION_PAUSE_TASK,
        raw_text=request.source_text,
        ai_payload=None,
        resolved_changes={
            "task_id": task.id,
            "task_data": {
                key: serialize_value(value)
                for key, value in new_values.items()
            },
            "proposed_changes": proposed_changes,
        },
        warnings=warnings,
        target_task_id=task.id,
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
    Confirms pending preview and writes changes to database.
    """

    preview = db.get(TaskPreview, preview_id)

    if preview is None:
        raise HTTPException(status_code=404, detail="Preview not found")

    if preview.status != PREVIEW_STATUS_PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Preview is not pending. Current status: {preview.status}",
        )

    if preview.warnings:
        raise HTTPException(
            status_code=400,
            detail="Preview contains warnings and cannot be confirmed.",
        )

    if preview.expires_at is not None and preview.expires_at < datetime.now(UTC):
        preview.status = PREVIEW_STATUS_EXPIRED
        db.commit()

        raise HTTPException(status_code=400, detail="Preview expired")

    if preview.action == ACTION_CREATE_TASK:
        return _confirm_create_task_preview(db=db, preview=preview)

    if preview.action == ACTION_CLOSE_TASK:
        return _confirm_close_task_preview(db=db, preview=preview)

    if preview.action == ACTION_START_TASK:
        return _confirm_start_task_preview(db=db, preview=preview)
    
    if preview.action == ACTION_PLAN_TASK:
        return _confirm_plan_task_preview(db=db, preview=preview)
    
    if preview.action == ACTION_PAUSE_TASK:
        return _confirm_pause_task_preview(db=db, preview=preview)

    if preview.action == ACTION_RESUME_TASK:
        return _confirm_resume_task_preview(db=db, preview=preview)

    raise HTTPException(
        status_code=400,
        detail=f"Unsupported preview action: {preview.action}",
    )

def create_resume_task_preview(
    db: Session,
    task_id: int,
    request: TaskResumePreviewRequest,
) -> TaskPreview:
    """
    Creates preview for resuming an existing paused task.
    """

    task = db.get(Task, task_id)

    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    warnings = []

    if task.fact_finish_date is not None:
        warnings.append("Task is already closed.")

    if task.fact_start_date is None:
        warnings.append("Task has not been started yet.")

    if task.auto_status != "Пауза":
        warnings.append("Task is not paused.")

    resume_description = request.resume_note or "Повернуто в роботу."

    new_values = {
        "auto_status": "В роботі",
        "short_status_description": resume_description,
    }

    old_values = {
        "auto_status": task.auto_status,
        "short_status_description": task.short_status_description,
    }

    proposed_changes = build_update_proposed_changes(
        old_data=old_values,
        new_data=new_values,
    )

    preview = TaskPreview(
        action=ACTION_RESUME_TASK,
        raw_text=request.source_text,
        ai_payload=None,
        resolved_changes={
            "task_id": task.id,
            "task_data": {
                key: serialize_value(value)
                for key, value in new_values.items()
            },
            "proposed_changes": proposed_changes,
        },
        warnings=warnings,
        target_task_id=task.id,
        status=PREVIEW_STATUS_PENDING,
        expires_at=datetime.now(UTC) + timedelta(hours=24),
        created_by=request.created_by,
    )

    db.add(preview)
    db.commit()
    db.refresh(preview)

    return preview

def _confirm_create_task_preview(
    db: Session,
    preview: TaskPreview,
) -> Task:
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


def _confirm_close_task_preview(
    db: Session,
    preview: TaskPreview,
) -> Task:
    if not preview.resolved_changes or "task_data" not in preview.resolved_changes:
        raise HTTPException(
            status_code=400,
            detail="Preview does not contain task data.",
        )

    task_id = preview.target_task_id or preview.resolved_changes.get("task_id")
    task = db.get(Task, task_id)

    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = deserialize_task_data(preview.resolved_changes["task_data"])

    for field, new_value in task_data.items():
        old_value = getattr(task, field)

        if serialize_value(old_value) == serialize_value(new_value):
            continue

        setattr(task, field, new_value)

        create_task_event(
            db=db,
            task_id=task.id,
            event_type="closed" if field == "auto_status" else "updated",
            field_name=field,
            old_value={"value": serialize_value(old_value)},
            new_value={"value": serialize_value(new_value)},
            comment="Task updated from confirmed close preview.",
            created_by=preview.created_by,
            source="preview",
        )

    preview.status = PREVIEW_STATUS_CONFIRMED
    preview.confirmed_at = datetime.now(UTC)
    preview.target_task_id = task.id

    db.commit()
    db.refresh(task)

    return task

def _confirm_start_task_preview(
    db: Session,
    preview: TaskPreview,
) -> Task:
    """
    Confirms start task preview and writes changes to database.
    """

    if not preview.resolved_changes or "task_data" not in preview.resolved_changes:
        raise HTTPException(
            status_code=400,
            detail="Preview does not contain task data.",
        )

    task_id = preview.target_task_id or preview.resolved_changes.get("task_id")
    task = db.get(Task, task_id)

    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = deserialize_task_data(preview.resolved_changes["task_data"])

    for field, new_value in task_data.items():
        old_value = getattr(task, field)

        if serialize_value(old_value) == serialize_value(new_value):
            continue

        setattr(task, field, new_value)

        if field == "fact_start_date":
            event_type = "started"
        elif field == "auto_status":
            event_type = "status_changed"
        else:
            event_type = "updated"

        create_task_event(
            db=db,
            task_id=task.id,
            event_type=event_type,
            field_name=field,
            old_value={"value": serialize_value(old_value)},
            new_value={"value": serialize_value(new_value)},
            comment="Task updated from confirmed start preview.",
            created_by=preview.created_by,
            source="preview",
        )

    preview.status = PREVIEW_STATUS_CONFIRMED
    preview.confirmed_at = datetime.now(UTC)
    preview.target_task_id = task.id

    db.commit()
    db.refresh(task)

    return task

def _confirm_plan_task_preview(
    db: Session,
    preview: TaskPreview,
) -> Task:
    """
    Confirms plan task preview and writes changes to database.
    """

    if not preview.resolved_changes or "task_data" not in preview.resolved_changes:
        raise HTTPException(
            status_code=400,
            detail="Preview does not contain task data.",
        )

    task_id = preview.target_task_id or preview.resolved_changes.get("task_id")
    task = db.get(Task, task_id)

    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = deserialize_task_data(preview.resolved_changes["task_data"])

    for field, new_value in task_data.items():
        old_value = getattr(task, field)

        if serialize_value(old_value) == serialize_value(new_value):
            continue

        setattr(task, field, new_value)

        if field == "fact_start_date":
            event_type = "planned"
        elif field == "planned_finish_date":
            event_type = "deadline_changed"
        elif field == "auto_status":
            event_type = "status_changed"
        else:
            event_type = "updated"

        create_task_event(
            db=db,
            task_id=task.id,
            event_type=event_type,
            field_name=field,
            old_value={"value": serialize_value(old_value)},
            new_value={"value": serialize_value(new_value)},
            comment="Task updated from confirmed plan preview.",
            created_by=preview.created_by,
            source="preview",
        )

    preview.status = PREVIEW_STATUS_CONFIRMED
    preview.confirmed_at = datetime.now(UTC)
    preview.target_task_id = task.id

    db.commit()
    db.refresh(task)

    return task

def _confirm_pause_task_preview(
    db: Session,
    preview: TaskPreview,
) -> Task:
    """
    Confirms pause task preview and writes changes to database.
    """

    if not preview.resolved_changes or "task_data" not in preview.resolved_changes:
        raise HTTPException(
            status_code=400,
            detail="Preview does not contain task data.",
        )

    task_id = preview.target_task_id or preview.resolved_changes.get("task_id")
    task = db.get(Task, task_id)

    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = deserialize_task_data(preview.resolved_changes["task_data"])

    for field, new_value in task_data.items():
        old_value = getattr(task, field)

        if serialize_value(old_value) == serialize_value(new_value):
            continue

        setattr(task, field, new_value)

        if field == "auto_status":
            event_type = "paused"
        else:
            event_type = "updated"

        create_task_event(
            db=db,
            task_id=task.id,
            event_type=event_type,
            field_name=field,
            old_value={"value": serialize_value(old_value)},
            new_value={"value": serialize_value(new_value)},
            comment="Task updated from confirmed pause preview.",
            created_by=preview.created_by,
            source="preview",
        )

    preview.status = PREVIEW_STATUS_CONFIRMED
    preview.confirmed_at = datetime.now(UTC)
    preview.target_task_id = task.id

    db.commit()
    db.refresh(task)

    return task

def _confirm_resume_task_preview(
    db: Session,
    preview: TaskPreview,
) -> Task:
    """
    Confirms resume task preview and writes changes to database.
    """

    if not preview.resolved_changes or "task_data" not in preview.resolved_changes:
        raise HTTPException(
            status_code=400,
            detail="Preview does not contain task data.",
        )

    task_id = preview.target_task_id or preview.resolved_changes.get("task_id")
    task = db.get(Task, task_id)

    if task is None or task.is_deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = deserialize_task_data(preview.resolved_changes["task_data"])

    for field, new_value in task_data.items():
        old_value = getattr(task, field)

        if serialize_value(old_value) == serialize_value(new_value):
            continue

        setattr(task, field, new_value)

        if field == "auto_status":
            event_type = "resumed"
        else:
            event_type = "updated"

        create_task_event(
            db=db,
            task_id=task.id,
            event_type=event_type,
            field_name=field,
            old_value={"value": serialize_value(old_value)},
            new_value={"value": serialize_value(new_value)},
            comment="Task updated from confirmed resume preview.",
            created_by=preview.created_by,
            source="preview",
        )

    preview.status = PREVIEW_STATUS_CONFIRMED
    preview.confirmed_at = datetime.now(UTC)
    preview.target_task_id = task.id

    db.commit()
    db.refresh(task)

    return task

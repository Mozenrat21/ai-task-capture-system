from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.task import Task
from app.models.task_event import TaskEvent
from app.schemas.task import (
    ConfirmPreviewRequest,
    ConfirmPreviewResponse,
    TaskClosePreviewRequest,
    TaskCreatePreviewRequest,
    TaskDetailResponse,
    TaskListResponse,
    TaskPlanPreviewRequest,
    TaskPreviewResponse,
    TaskStartPreviewRequest,
    TaskPausePreviewRequest,
    TaskResumePreviewRequest,
    TaskUpdatePreviewRequest
)
from app.services.preview_service import (
    confirm_task_preview,
    create_close_task_preview,
    create_plan_task_preview,
    create_start_task_preview,
    create_pause_task_preview,
    create_resume_task_preview,
    create_update_task_preview,
    create_task_preview,
)
from app.schemas.task_event import TaskEventResponse
from app.schemas.ai_parser import AIParseTaskRequest
from app.services.ai_parser_service import parse_task_text


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

@router.post("/ai-preview", response_model=TaskPreviewResponse)
def preview_create_task_from_ai_text(
    request: AIParseTaskRequest,
    db: Session = Depends(get_db),
):
    """
    Creates task preview from raw Ukrainian text.

    Flow:
    raw_text -> mock AI parser -> structured task payload -> preview.
    """

    parsed_task = parse_task_text(
        raw_text=request.raw_text,
        created_by=request.created_by,
    )

    preview_request = TaskCreatePreviewRequest(
        task_title=parsed_task.task_title,
        goal=parsed_task.goal,
        task_type_id=parsed_task.task_type_id,
        business_area=parsed_task.business_area,
        customer=parsed_task.customer,
        priority_id=parsed_task.priority_id,
        complexity_id=parsed_task.complexity_id,
        executor=parsed_task.executor,
        planned_finish_date=parsed_task.planned_finish_date,
        source_text=parsed_task.source_text,
        created_by=parsed_task.created_by,
    )

    preview = create_task_preview(
        db=db,
        request=preview_request,
    )

    resolved_changes = preview.resolved_changes or {}
    proposed_changes = resolved_changes.get("proposed_changes", [])

    return TaskPreviewResponse(
        preview_id=preview.id,
        action=preview.action,
        target_task_id=preview.target_task_id,
        proposed_changes=proposed_changes,
        warnings=preview.warnings or [],
        can_confirm=len(preview.warnings or []) == 0,
    )

@router.post("/preview", response_model=TaskPreviewResponse)
def preview_create_task(
    request: TaskCreatePreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Creates task preview.

    This endpoint does not write task to tasks table.
    It only prepares proposed changes for user confirmation.
    """

    preview = create_task_preview(db=db, request=request)

    resolved_changes = preview.resolved_changes or {}
    proposed_changes = resolved_changes.get("proposed_changes", [])

    return TaskPreviewResponse(
        preview_id=preview.id,
        action=preview.action,
        target_task_id=preview.target_task_id,
        proposed_changes=proposed_changes,
        warnings=preview.warnings or [],
        can_confirm=len(preview.warnings or []) == 0,
    )


@router.post("/confirm", response_model=ConfirmPreviewResponse)
def confirm_preview(
    request: ConfirmPreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Confirms pending preview and writes changes to database.
    """

    task = confirm_task_preview(db=db, preview_id=request.preview_id)

    return ConfirmPreviewResponse(
        status="confirmed",
        task_id=task.id,
        message="Preview confirmed successfully.",
    )

@router.post("/{task_id}/close", response_model=TaskPreviewResponse)
def preview_close_task(
    task_id: int,
    request: TaskClosePreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Creates preview for closing existing task.

    This endpoint does not update task immediately.
    It only prepares proposed changes for user confirmation.
    """

    preview = create_close_task_preview(
        db=db,
        task_id=task_id,
        request=request,
    )

    resolved_changes = preview.resolved_changes or {}
    proposed_changes = resolved_changes.get("proposed_changes", [])

    return TaskPreviewResponse(
        preview_id=preview.id,
        action=preview.action,
        target_task_id=preview.target_task_id,
        proposed_changes=proposed_changes,
        warnings=preview.warnings or [],
        can_confirm=len(preview.warnings or []) == 0,
    )

def build_task_list_response(task: Task) -> TaskListResponse:
    """
    Converts Task SQLAlchemy model to API list response.

    We keep this mapping explicit because response includes dictionary names
    from related tables.
    """

    return TaskListResponse(
        id=task.id,
        task_title=task.task_title,
        goal=task.goal,
        auto_status=task.auto_status,
        business_area=task.business_area,
        customer=task.customer,
        executor=task.executor,
        planned_finish_date=task.planned_finish_date,
        fact_start_date=task.fact_start_date,
        fact_finish_date=task.fact_finish_date,
        fact_hours=task.fact_hours,
        auto_task_score=task.auto_task_score,
        short_status_description=task.short_status_description,
        created_at=task.created_at,
        updated_at=task.updated_at,
        task_type_name=task.task_type.name if task.task_type else None,
        priority_name=task.priority.name if task.priority else None,
        complexity_name=task.complexity.name if task.complexity else None,
    )


def build_task_detail_response(task: Task) -> TaskDetailResponse:
    """
    Converts Task SQLAlchemy model to detailed API response.
    """

    base = build_task_list_response(task)

    return TaskDetailResponse(
        **base.model_dump(),
        task_type_id=task.task_type_id,
        priority_id=task.priority_id,
        complexity_id=task.complexity_id,
        extra_column=task.extra_column,
        plan_fact=task.plan_fact,
        source_text=task.source_text,
        ai_confidence=task.ai_confidence,
        created_by=task.created_by,
        is_deleted=task.is_deleted,
    )

@router.post("/{task_id}/start", response_model=TaskPreviewResponse)
def preview_start_task(
    task_id: int,
    request: TaskStartPreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Creates preview for starting existing task.

    This endpoint does not update task immediately.
    It only prepares proposed changes for user confirmation.
    """

    preview = create_start_task_preview(
        db=db,
        task_id=task_id,
        request=request,
    )

    resolved_changes = preview.resolved_changes or {}
    proposed_changes = resolved_changes.get("proposed_changes", [])

    return TaskPreviewResponse(
        preview_id=preview.id,
        action=preview.action,
        target_task_id=preview.target_task_id,
        proposed_changes=proposed_changes,
        warnings=preview.warnings or [],
        can_confirm=len(preview.warnings or []) == 0,
    )

@router.post("/{task_id}/plan", response_model=TaskPreviewResponse)
def preview_plan_task(
    task_id: int,
    request: TaskPlanPreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Creates preview for planning existing task.

    This endpoint does not update task immediately.
    It only prepares proposed changes for user confirmation.
    """

    preview = create_plan_task_preview(
        db=db,
        task_id=task_id,
        request=request,
    )

    resolved_changes = preview.resolved_changes or {}
    proposed_changes = resolved_changes.get("proposed_changes", [])

    return TaskPreviewResponse(
        preview_id=preview.id,
        action=preview.action,
        target_task_id=preview.target_task_id,
        proposed_changes=proposed_changes,
        warnings=preview.warnings or [],
        can_confirm=len(preview.warnings or []) == 0,
    )

@router.post("/{task_id}/pause", response_model=TaskPreviewResponse)
def preview_pause_task(
    task_id: int,
    request: TaskPausePreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Creates preview for pausing existing task.

    This endpoint does not update task immediately.
    It only prepares proposed changes for user confirmation.
    """

    preview = create_pause_task_preview(
        db=db,
        task_id=task_id,
        request=request,
    )

    resolved_changes = preview.resolved_changes or {}
    proposed_changes = resolved_changes.get("proposed_changes", [])

    return TaskPreviewResponse(
        preview_id=preview.id,
        action=preview.action,
        target_task_id=preview.target_task_id,
        proposed_changes=proposed_changes,
        warnings=preview.warnings or [],
        can_confirm=len(preview.warnings or []) == 0,
    )

@router.post("/{task_id}/resume", response_model=TaskPreviewResponse)
def preview_resume_task(
    task_id: int,
    request: TaskResumePreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Creates preview for resuming paused task.
    """

    preview = create_resume_task_preview(
        db=db,
        task_id=task_id,
        request=request,
    )

    resolved_changes = preview.resolved_changes or {}
    proposed_changes = resolved_changes.get("proposed_changes", [])

    return TaskPreviewResponse(
        preview_id=preview.id,
        action=preview.action,
        target_task_id=preview.target_task_id,
        proposed_changes=proposed_changes,
        warnings=preview.warnings or [],
        can_confirm=len(preview.warnings or []) == 0,
    )

@router.post("/{task_id}/update", response_model=TaskPreviewResponse)
def preview_update_task(
    task_id: int,
    request: TaskUpdatePreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Creates preview for updating existing task.

    This endpoint does not update task immediately.
    It only prepares proposed changes for user confirmation.
    """

    preview = create_update_task_preview(
        db=db,
        task_id=task_id,
        request=request,
    )

    resolved_changes = preview.resolved_changes or {}
    proposed_changes = resolved_changes.get("proposed_changes", [])

    return TaskPreviewResponse(
        preview_id=preview.id,
        action=preview.action,
        target_task_id=preview.target_task_id,
        proposed_changes=proposed_changes,
        warnings=preview.warnings or [],
        can_confirm=len(preview.warnings or []) == 0,
    )

@router.get("", response_model=list[TaskListResponse])
def list_tasks(
    db: Session = Depends(get_db),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    Returns task list.

    Supports basic filtering by auto_status and text search.
    """

    statement = (
        select(Task)
        .options(
            joinedload(Task.task_type),
            joinedload(Task.priority),
            joinedload(Task.complexity),
        )
        .where(Task.is_deleted.is_(False))
        .order_by(Task.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    if status:
        statement = statement.where(Task.auto_status == status)

    if search:
        search_pattern = f"%{search}%"
        statement = statement.where(
            or_(
                Task.task_title.ilike(search_pattern),
                Task.goal.ilike(search_pattern),
                Task.short_status_description.ilike(search_pattern),
                Task.business_area.ilike(search_pattern),
                Task.customer.ilike(search_pattern),
            )
        )

    tasks = db.scalars(statement).all()

    return [build_task_list_response(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskDetailResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns task details by ID.
    """

    statement = (
        select(Task)
        .options(
            joinedload(Task.task_type),
            joinedload(Task.priority),
            joinedload(Task.complexity),
        )
        .where(Task.id == task_id, Task.is_deleted.is_(False))
    )

    task = db.scalars(statement).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return build_task_detail_response(task)


@router.get("/{task_id}/events", response_model=list[TaskEventResponse])
def get_task_events(
    task_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns task event history.
    """

    task_exists_statement = select(Task.id).where(
        Task.id == task_id,
        Task.is_deleted.is_(False),
    )

    task_id_from_db = db.scalar(task_exists_statement)

    if task_id_from_db is None:
        raise HTTPException(status_code=404, detail="Task not found")

    events_statement = (
        select(TaskEvent)
        .where(TaskEvent.task_id == task_id)
        .order_by(TaskEvent.created_at.desc(), TaskEvent.id.desc())
    )

    return db.scalars(events_statement).all()
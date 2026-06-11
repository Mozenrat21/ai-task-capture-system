from sqlalchemy.orm import Session

from app.models.task_event import TaskEvent


def create_task_event(
    db: Session,
    task_id: int,
    event_type: str,
    field_name: str | None = None,
    old_value: dict | None = None,
    new_value: dict | None = None,
    comment: str | None = None,
    created_by: str | None = None,
    source: str = "api",
) -> TaskEvent:
    """
    Creates task event record.

    This is the audit trail for task changes.
    """

    event = TaskEvent(
        task_id=task_id,
        event_type=event_type,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        comment=comment,
        created_by=created_by,
        source=source,
    )

    db.add(event)

    return event
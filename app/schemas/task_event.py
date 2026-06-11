from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TaskEventResponse(BaseModel):
    id: int
    task_id: int
    event_type: str
    field_name: str | None = None
    old_value: dict | None = None
    new_value: dict | None = None
    comment: str | None = None
    created_at: datetime
    created_by: str | None = None
    source: str

    model_config = ConfigDict(from_attributes=True)
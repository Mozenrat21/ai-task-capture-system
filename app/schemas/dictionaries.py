from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PriorityResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    response_time: str | None = None
    coefficient: Decimal
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ComplexityResponse(BaseModel):
    id: int
    code: str
    name: str
    description: str | None = None
    expected_duration: str | None = None
    coefficient: Decimal
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TaskTypeResponse(BaseModel):
    id: int
    code: str
    name: str
    base_hours: Decimal
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TaskScoreMatrixResponse(BaseModel):
    id: int
    priority_code: str
    complexity_code: str
    score_multiplier: Decimal
    comment: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
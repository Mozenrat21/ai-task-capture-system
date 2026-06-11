from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dictionaries import (
    ComplexityDict,
    PriorityDict,
    TaskScoreMatrix,
    TaskTypeDict,
)
from app.schemas.dictionaries import (
    ComplexityResponse,
    PriorityResponse,
    TaskScoreMatrixResponse,
    TaskTypeResponse,
)

router = APIRouter(
    prefix="/dicts",
    tags=["dictionaries"],
)


@router.get("/priorities", response_model=list[PriorityResponse])
def get_priorities(db: Session = Depends(get_db)):
    """
    Returns active task priority dictionary.
    """

    statement = (
        select(PriorityDict)
        .where(PriorityDict.is_active.is_(True))
        .order_by(PriorityDict.sort_order)
    )

    return db.scalars(statement).all()


@router.get("/complexities", response_model=list[ComplexityResponse])
def get_complexities(db: Session = Depends(get_db)):
    """
    Returns active task complexity dictionary.
    """

    statement = (
        select(ComplexityDict)
        .where(ComplexityDict.is_active.is_(True))
        .order_by(ComplexityDict.sort_order)
    )

    return db.scalars(statement).all()


@router.get("/task-types", response_model=list[TaskTypeResponse])
def get_task_types(db: Session = Depends(get_db)):
    """
    Returns active task type dictionary.
    """

    statement = (
        select(TaskTypeDict)
        .where(TaskTypeDict.is_active.is_(True))
        .order_by(TaskTypeDict.sort_order)
    )

    return db.scalars(statement).all()


@router.get("/task-score-matrix", response_model=list[TaskScoreMatrixResponse])
def get_task_score_matrix(db: Session = Depends(get_db)):
    """
    Returns active task score matrix.

    This matrix is used to explain how priority and complexity
    affect the automatic task score.
    """

    statement = (
        select(TaskScoreMatrix)
        .where(TaskScoreMatrix.is_active.is_(True))
        .order_by(
            TaskScoreMatrix.priority_code,
            TaskScoreMatrix.complexity_code,
        )
    )

    return db.scalars(statement).all()
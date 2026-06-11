from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Task(Base):
    """
    Main task table.

    Stores task data migrated from the current Excel logic:
    title, goal, task type, business area, priority, complexity,
    planned/factual dates, factual hours and calculated fields.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    task_title: Mapped[str] = mapped_column(Text, nullable=False)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)

    task_type_id: Mapped[int | None] = mapped_column(
        ForeignKey("task_type_dict.id"),
        nullable=True,
    )

    business_area: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer: Mapped[str | None] = mapped_column(String(255), nullable=True)

    auto_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Оцінка",
    )

    priority_id: Mapped[int | None] = mapped_column(
        ForeignKey("priority_dict.id"),
        nullable=True,
    )
    complexity_id: Mapped[int | None] = mapped_column(
        ForeignKey("complexity_dict.id"),
        nullable=True,
    )

    auto_task_score: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    executor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    extra_column: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_fact: Mapped[str | None] = mapped_column(Text, nullable=True)

    fact_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_finish_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    fact_finish_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    fact_hours: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )

    short_status_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    ai_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        nullable=True,
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    task_type = relationship("TaskTypeDict", back_populates="tasks")
    priority = relationship("PriorityDict", back_populates="tasks")
    complexity = relationship("ComplexityDict", back_populates="tasks")

    events = relationship(
        "TaskEvent",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    previews = relationship(
        "TaskPreview",
        back_populates="target_task",
    )
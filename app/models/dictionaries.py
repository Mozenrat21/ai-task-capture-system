from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PriorityDict(Base):
    __tablename__ = "priority_dict"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_time: Mapped[str | None] = mapped_column(String(100), nullable=True)
    coefficient: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tasks = relationship("Task", back_populates="priority")


class ComplexityDict(Base):
    __tablename__ = "complexity_dict"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_duration: Mapped[str | None] = mapped_column(String(100), nullable=True)
    coefficient: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tasks = relationship("Task", back_populates="complexity")


class TaskTypeDict(Base):
    __tablename__ = "task_type_dict"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    base_hours: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tasks = relationship("Task", back_populates="task_type")


class TaskScoreMatrix(Base):
    __tablename__ = "task_score_matrix"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    priority_code: Mapped[str] = mapped_column(String(50), nullable=False)
    complexity_code: Mapped[str] = mapped_column(String(50), nullable=False)
    score_multiplier: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
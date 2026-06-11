from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TaskPreview(Base):
    """
    Stores pending task changes before confirmation.

    Important rule:
    no critical task changes are written directly to tasks table.
    First we create preview, then user confirms it,
    then backend applies changes in a controlled way.
    """

    __tablename__ = "task_previews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    ai_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    resolved_changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    warnings: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    target_task_id: Mapped[int | None] = mapped_column(
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    target_task = relationship("Task", back_populates="previews")
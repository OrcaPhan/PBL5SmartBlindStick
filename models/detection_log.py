"""
Model cho bảng detection_logs.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.stick import Stick


class DetectionLog(Base):
    """Log kết quả nhận diện vật thể từ AI."""

    __tablename__ = "detection_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stick_id: Mapped[str | None] = mapped_column(
        String(20),
        ForeignKey("sticks.stick_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    object_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    stick: Mapped["Stick | None"] = relationship(
        "Stick",
        back_populates="detection_logs",
    )

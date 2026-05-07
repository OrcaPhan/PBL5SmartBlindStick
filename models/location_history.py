"""
Model cho bảng location_history.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.stick import Stick


class LocationHistory(Base):
    """Lịch sử vị trí và pin của thiết bị stick."""

    __tablename__ = "location_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stick_id: Mapped[str | None] = mapped_column(
        String(20),
        ForeignKey("sticks.stick_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    battery: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    stick: Mapped["Stick | None"] = relationship(
        "Stick",
        back_populates="location_histories",
    )

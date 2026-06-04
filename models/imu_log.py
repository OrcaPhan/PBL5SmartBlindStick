"""
Model cho bảng imu_logs.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.stick import Stick


class IMULog(Base):
    """Lịch sử gia tốc và vận tốc góc của thiết bị stick."""

    __tablename__ = "imu_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    stick_id: Mapped[str | None] = mapped_column(
        String(20),
        ForeignKey("sticks.stick_id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    acc_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    acc_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    acc_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    gyro_x: Mapped[float | None] = mapped_column(Float, nullable=True)
    gyro_y: Mapped[float | None] = mapped_column(Float, nullable=True)
    gyro_z: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    stick: Mapped["Stick | None"] = relationship(
        "Stick",
        back_populates="imu_logs",
    )

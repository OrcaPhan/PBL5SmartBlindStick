"""
Model cho bảng sticks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Float, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.detection_log import DetectionLog
    from models.location_history import LocationHistory
    from models.imu_log import IMULog
    from models.user import User


class Stick(Base):
    """Thông tin cây gậy định danh theo stick_id."""

    __tablename__ = "sticks"

    stick_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    imu_offset_pitch: Mapped[float] = mapped_column(Float, default=0.0, server_default=text("0.0"))
    imu_offset_roll: Mapped[float] = mapped_column(Float, default=0.0, server_default=text("0.0"))

    owner: Mapped["User | None"] = relationship(
        "User",
        back_populates="sticks",
    )
    location_histories: Mapped[list["LocationHistory"]] = relationship(
        "LocationHistory",
        back_populates="stick",
        cascade="all, delete-orphan",
    )
    detection_logs: Mapped[list["DetectionLog"]] = relationship(
        "DetectionLog",
        back_populates="stick",
        cascade="all, delete-orphan",
    )
    imu_logs: Mapped[list["IMULog"]] = relationship(
        "IMULog",
        back_populates="stick",
        cascade="all, delete-orphan",
    )

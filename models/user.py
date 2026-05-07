"""
Model cho bảng users.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.detection_log import DetectionLog
    from models.location_history import LocationHistory
    from models.relationship import Relationship
    from models.stick import Stick


class User(Base):
    """Người dùng hệ thống: blind_user hoặc caretaker."""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('blind_user', 'caretaker')",
            name="users_role_check",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(15), nullable=True)

    sticks: Mapped[list["Stick"]] = relationship(
        "Stick",
        back_populates="owner",
        cascade="all, delete-orphan",
    )

    caretaker_links: Mapped[list["Relationship"]] = relationship(
        "Relationship",
        foreign_keys="Relationship.caretaker_id",
        back_populates="caretaker",
        cascade="all, delete-orphan",
    )
    blind_user_links: Mapped[list["Relationship"]] = relationship(
        "Relationship",
        foreign_keys="Relationship.blind_user_id",
        back_populates="blind_user",
        cascade="all, delete-orphan",
    )

    # Quan hệ nhiều-nhiều: caretaker -> nhiều blind_user.
    blind_users: Mapped[list["User"]] = relationship(
        "User",
        secondary="relationships",
        primaryjoin="User.id == Relationship.caretaker_id",
        secondaryjoin="User.id == Relationship.blind_user_id",
        back_populates="caretakers",
        overlaps="caretaker_links,blind_user_links,caretaker,blind_user",
    )
    # Quan hệ nhiều-nhiều ngược lại: blind_user <- nhiều caretaker.
    caretakers: Mapped[list["User"]] = relationship(
        "User",
        secondary="relationships",
        primaryjoin="User.id == Relationship.blind_user_id",
        secondaryjoin="User.id == Relationship.caretaker_id",
        back_populates="blind_users",
        overlaps="caretaker_links,blind_user_links,caretaker,blind_user",
    )

    location_histories: Mapped[list["LocationHistory"]] = relationship(
        "LocationHistory",
        secondary="sticks",
        primaryjoin="User.id == Stick.owner_id",
        secondaryjoin="Stick.stick_id == LocationHistory.stick_id",
        viewonly=True,
    )
    detection_logs: Mapped[list["DetectionLog"]] = relationship(
        "DetectionLog",
        secondary="sticks",
        primaryjoin="User.id == Stick.owner_id",
        secondaryjoin="Stick.stick_id == DetectionLog.stick_id",
        viewonly=True,
    )

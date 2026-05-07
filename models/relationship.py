"""
Model cho bảng relationships (liên kết caretaker và blind_user).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.user import User


class Relationship(Base):
    """
    Bảng trung gian many-to-many giữa User (caretaker) và User (blind_user).
    """

    __tablename__ = "relationships"

    caretaker_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    blind_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    caretaker: Mapped["User"] = relationship(
        "User",
        foreign_keys=[caretaker_id],
        back_populates="caretaker_links",
        overlaps="blind_users,caretakers,blind_user_links",
    )
    blind_user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[blind_user_id],
        back_populates="blind_user_links",
        overlaps="blind_users,caretakers,caretaker_links",
    )

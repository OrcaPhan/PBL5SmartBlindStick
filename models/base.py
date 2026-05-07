"""
Khai báo Base chung cho toàn bộ SQLAlchemy models.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class cho toàn bộ model."""


"""
Repository thao tác dữ liệu GPS từ phần cứng.
"""

from datetime import datetime

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.location_history import LocationHistory
from schemas.hardware_schema import HardwareGpsIn


async def insert_location_history(
    db: AsyncSession,
    payload: HardwareGpsIn,
) -> LocationHistory:
    """
    Ghi một bản ghi GPS vào bảng location_history.
    """
    location_log = LocationHistory(
        stick_id=payload.stick_id,
        lat=payload.lat,
        lon=payload.lon,
        battery=payload.battery,
    )
    db.add(location_log)
    await db.commit()
    await db.refresh(location_log)
    return location_log


async def get_latest_location_by_stick_id(
    db: AsyncSession,
    stick_id: str,
) -> LocationHistory | None:
    """
    Lay vi tri moi nhat cua 1 stick theo timestamp giam dan.
    """
    stmt: Select[tuple[LocationHistory]] = (
        select(LocationHistory)
        .where(LocationHistory.stick_id == stick_id)
        .order_by(LocationHistory.timestamp.desc(), LocationHistory.id.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_location_history_by_session(
    db: AsyncSession,
    stick_id: str,
    session_start: datetime,
    session_end: datetime,
    limit: int,
) -> list[LocationHistory]:
    """
    Lay danh sach diem GPS theo khoang thoi gian (1 buoi) cho 1 stick.
    """
    stmt: Select[tuple[LocationHistory]] = (
        select(LocationHistory)
        .where(LocationHistory.stick_id == stick_id)
        .where(LocationHistory.timestamp >= session_start)
        .where(LocationHistory.timestamp <= session_end)
        .order_by(LocationHistory.timestamp.asc(), LocationHistory.id.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

"""
Repository thao tác dữ liệu GPS từ phần cứng.
"""

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

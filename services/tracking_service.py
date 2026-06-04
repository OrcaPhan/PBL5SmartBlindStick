"""
Service xử lý nghiệp vụ tracking từ dữ liệu phần cứng.
"""

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.hardware_repo import (
    get_latest_location_by_stick_id,
    get_location_history_by_session,
    insert_location_history,
)
from schemas.hardware_schema import HardwareGpsIn, SessionRouteOut


async def receive_gps_data(
    db: AsyncSession,
    payload: HardwareGpsIn,
):
    """
    Tiếp nhận dữ liệu GPS từ controller và ghi xuống database.
    """
    try:
        return await insert_location_history(db=db, payload=payload)
    except IntegrityError as exc:
        # Thường xảy ra khi stick_id không tồn tại trong bảng sticks.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Du lieu GPS khong hop le hoac stick_id khong ton tai.",
        ) from exc
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Loi he thong khi luu du lieu GPS.",
        ) from exc


async def get_current_location(
    db: AsyncSession,
    stick_id: str,
):
    """
    Lay vi tri hien tai cua stick de app cap nhat lien tuc.
    """
    try:
        location = await get_latest_location_by_stick_id(db=db, stick_id=stick_id)
        if location is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chua co du lieu vi tri cho stick_id nay.",
            )
        return location
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Loi he thong khi lay vi tri hien tai.",
        ) from exc


async def get_route_by_session(
    db: AsyncSession,
    stick_id: str,
    session_start: datetime,
    session_end: datetime,
    limit: int = 1000,
) -> SessionRouteOut:
    """
    Lay danh sach lo trinh di chuyen theo buoi cua 1 stick.
    """
    if session_start >= session_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_start phai nho hon session_end.",
        )
    if limit <= 0 or limit > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="limit phai trong khoang 1..5000.",
        )

    # Convert aware datetimes to naive since SQLAlchemy column is DateTime without timezone
    if session_start.tzinfo is not None:
        session_start = session_start.replace(tzinfo=None)
    if session_end.tzinfo is not None:
        session_end = session_end.replace(tzinfo=None)

    try:
        points = await get_location_history_by_session(
            db=db,
            stick_id=stick_id,
            session_start=session_start,
            session_end=session_end,
            limit=limit,
        )
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Loi he thong khi lay lo trinh theo buoi.",
        ) from exc

    return SessionRouteOut(
        stick_id=stick_id,
        session_start=session_start,
        session_end=session_end,
        total_points=len(points),
        points=points,
    )

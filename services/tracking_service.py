"""
Service xử lý nghiệp vụ tracking từ dữ liệu phần cứng.
"""

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from repositories.hardware_repo import insert_location_history
from schemas.hardware_schema import HardwareGpsIn


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

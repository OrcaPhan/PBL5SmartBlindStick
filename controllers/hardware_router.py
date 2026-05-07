"""
Router cho các API phần cứng.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.hardware_schema import HardwareGpsIn, HardwareGpsOut
from services.tracking_service import receive_gps_data

router = APIRouter(prefix="/api/hardware", tags=["Hardware"])


@router.post(
    "/gps",
    response_model=HardwareGpsOut,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_gps_data(
    payload: HardwareGpsIn,
    db: AsyncSession = Depends(get_db),
) -> HardwareGpsOut:
    """
    Nhận dữ liệu định vị từ phần cứng và lưu vào location_history.
    """
    try:
        location_log = await receive_gps_data(db=db, payload=payload)
        return HardwareGpsOut.model_validate(location_log)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the xu ly du lieu GPS tu phan cung.",
        ) from exc

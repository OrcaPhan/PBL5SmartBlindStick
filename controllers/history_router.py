"""
Router quản lý các API liên quan đến lịch sử phát hiện vật cản.
"""

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import get_current_user
from models.user import User
from repositories.history_repo import get_detections_by_hour, get_history_summary
from repositories.stick_repo import get_stick_by_owner, get_sticks_by_caretaker
from schemas.history import DetectionLogResponse, HistorySummaryResponse

router = APIRouter(prefix="/api/history", tags=["History"])


async def verify_stick_access(db: AsyncSession, stick_id: str, user: User) -> None:
    """
    Kiểm tra xem user hiện tại có quyền truy cập vào stick_id này không.
    - BLIND_USER: chỉ xem được gậy của mình.
    - CARETAKER: xem được gậy của những người mình đang quản lý.
    """
    if user.role == "blind_user":
        my_stick = await get_stick_by_owner(db, user.id)
        if not my_stick or my_stick.stick_id != stick_id:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền xem lịch sử của gậy này."
            )
    elif user.role == "caretaker":
        allowed_sticks = await get_sticks_by_caretaker(db, user.id)
        allowed_stick_ids = [s.stick_id for s in allowed_sticks]
        if stick_id not in allowed_stick_ids:
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền xem lịch sử của gậy này."
            )


@router.get("/summary", response_model=HistorySummaryResponse)
async def api_get_history_summary(
    stick_id: str = Query(..., description="ID của gậy (VD: STK001)"),
    target_date: date = Query(..., alias="date", description="Ngày xem lịch sử (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy thông tin tổng quan của lịch sử trong một ngày cụ thể.
    Bao gồm: tổng ảnh, số khung giờ, độ tin cậy trung bình, và danh sách các giờ (mảng số nguyên giảm dần).
    """
    await verify_stick_access(db, stick_id, current_user)
    summary = await get_history_summary(db, stick_id, target_date)
    return HistorySummaryResponse(**summary)


@router.get("/detections", response_model=List[DetectionLogResponse])
async def api_get_detections_by_hour(
    stick_id: str = Query(..., description="ID của gậy (VD: STK001)"),
    target_date: date = Query(..., alias="date", description="Ngày xem lịch sử (YYYY-MM-DD)"),
    hour: int = Query(..., ge=0, le=23, description="Khung giờ cần xem (0-23)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lấy chi tiết danh sách ảnh (log) đã phát hiện trong một khung giờ cụ thể của một ngày.
    """
    await verify_stick_access(db, stick_id, current_user)
    detections = await get_detections_by_hour(db, stick_id, target_date, hour)
    return detections

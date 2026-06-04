"""
Router cho các API phần cứng.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.websocket_manager import ws_manager
from schemas.hardware_schema import (
    CurrentLocationOut,
    HardwareGpsIn,
    HardwareGpsOut,
    SessionRouteOut,
)
from services.tracking_service import (
    get_current_location,
    get_route_by_session,
    receive_gps_data,
)

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
        out_data = HardwareGpsOut.model_validate(location_log)
        
        # Phát qua WebSocket cho các client đang kết nối
        await ws_manager.broadcast_location(payload.stick_id, out_data.model_dump())
        
        return out_data
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the xu ly du lieu GPS tu phan cung.",
        ) from exc


@router.get(
    "/{stick_id}/current-location",
    response_model=CurrentLocationOut,
    status_code=status.HTTP_200_OK,
)
async def fetch_current_location(
    stick_id: str,
    db: AsyncSession = Depends(get_db),
) -> CurrentLocationOut:
    """
    API cho app lay vi tri hien tai cua stick (goi lap de cap nhat lien tuc).
    """
    try:
        location = await get_current_location(db=db, stick_id=stick_id)
        return CurrentLocationOut.model_validate(location)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the lay vi tri hien tai.",
        ) from exc


@router.get(
    "/{stick_id}/session-route",
    response_model=SessionRouteOut,
    status_code=status.HTTP_200_OK,
)
async def fetch_session_route(
    stick_id: str,
    session_start: datetime,
    session_end: datetime,
    limit: int = 1000,
    db: AsyncSession = Depends(get_db),
) -> SessionRouteOut:
    """
    API cho app lay lo trinh di chuyen theo 1 buoi (khoang thoi gian).
    """
    try:
        return await get_route_by_session(
            db=db,
            stick_id=stick_id,
            session_start=session_start,
            session_end=session_end,
            limit=limit,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the lay lo trinh theo buoi.",
        ) from exc


@router.post(
    "/{stick_id}/calibrate",
    status_code=status.HTTP_200_OK,
)
async def calibrate_stick_imu(
    stick_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    API hiệu chuẩn thiết bị IMU.
    Khi người dùng giữ gậy đứng thẳng, gọi API này sẽ lưu góc lệch hiện tại (Pitch, Roll) làm mốc 0.
    """
    from models.imu_log import IMULog
    from models.stick import Stick
    from sqlalchemy import select
    import math

    # 1. Kiểm tra xem stick có tồn tại không
    stmt_stick = select(Stick).where(Stick.stick_id == stick_id)
    res_stick = await db.execute(stmt_stick)
    stick = res_stick.scalar_one_or_none()
    if not stick:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tìm thấy thiết bị gậy với ID đã cung cấp.",
        )

    # 2. Lấy bản ghi IMU gần nhất của gậy này
    stmt_imu = (
        select(IMULog)
        .where(IMULog.stick_id == stick_id)
        .order_by(IMULog.timestamp.desc(), IMULog.id.desc())
        .limit(1)
    )
    res_imu = await db.execute(stmt_imu)
    latest_imu = res_imu.scalar_one_or_none()
    if not latest_imu:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chưa có dữ liệu IMU từ thiết bị này để thực hiện hiệu chuẩn.",
        )

    # 3. Tính toán góc Pitch và Roll hiện tại để làm góc lệch (Offset)
    ax = latest_imu.acc_x or 0.0
    ay = latest_imu.acc_y or 0.0
    az = latest_imu.acc_z or 0.0

    raw_pitch = math.atan2(ay, math.sqrt(ax**2 + az**2)) * (180.0 / math.pi)
    raw_roll = math.atan2(-ax, az) * (180.0 / math.pi)

    # 4. Lưu lại góc lệch vào bảng sticks
    stick.imu_offset_pitch = raw_pitch
    stick.imu_offset_roll = raw_roll

    await db.commit()
    await db.refresh(stick)

    return {
        "status": "success",
        "message": "Hiệu chuẩn thành công. Đã thiết lập góc lệch mốc 0.",
        "stick_id": stick_id,
        "offsets": {
            "pitch": round(raw_pitch, 2),
            "roll": round(raw_roll, 2)
        }
    }


@router.websocket("/ws/{stick_id}")
async def websocket_location_endpoint(websocket: WebSocket, stick_id: str):
    """
    WebSocket endpoint để Frontend kết nối và nhận tọa độ ngay khi phần cứng đẩy lên.
    """
    await ws_manager.connect(websocket, stick_id)
    try:
        while True:
            # Giữ kết nối, chờ client ngắt kết nối
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, stick_id)

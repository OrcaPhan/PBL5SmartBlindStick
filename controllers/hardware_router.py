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

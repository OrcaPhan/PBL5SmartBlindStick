"""
Schemas cho luồng phần cứng gửi dữ liệu GPS.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HardwareGpsIn(BaseModel):
    """Schema validate body GPS gửi từ thiết bị phần cứng."""

    stick_id: str = Field(..., min_length=1, max_length=20)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    battery: int = Field(..., ge=0, le=100)


class HardwareGpsOut(BaseModel):
    """Schema response sau khi ghi dữ liệu GPS thành công."""

    id: int
    stick_id: str
    lat: float
    lon: float
    battery: int
    timestamp: datetime | None

    model_config = ConfigDict(from_attributes=True)


class CurrentLocationOut(BaseModel):
    """Schema vi tri hien tai de app cap nhat lien tuc theo tung gay."""

    stick_id: str
    lat: float
    lon: float
    battery: int
    timestamp: datetime | None

    model_config = ConfigDict(from_attributes=True)


class RoutePointOut(BaseModel):
    """Schema 1 diem trong lo trinh di chuyen."""

    lat: float
    lon: float
    battery: int
    timestamp: datetime | None

    model_config = ConfigDict(from_attributes=True)


class SessionRouteOut(BaseModel):
    """Schema danh sach lo trinh theo buoi de app hien thi lich su."""

    stick_id: str
    session_start: datetime
    session_end: datetime
    total_points: int
    points: list[RoutePointOut]

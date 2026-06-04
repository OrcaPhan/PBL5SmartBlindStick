"""
Schema định nghĩa dữ liệu trả về cho phần Lịch sử (History).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class HistorySummaryResponse(BaseModel):
    total_images: int
    total_timeframes: int
    average_confidence: float
    available_hours: List[int]


class DetectionLogResponse(BaseModel):
    id: int
    stick_id: str
    object_name: Optional[str] = None
    confidence: Optional[float] = None
    image_url: Optional[str] = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("image_url", mode="after")
    @classmethod
    def format_image_url(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return v
        from core.minio_client import minio_client
        return minio_client.get_full_url(v)

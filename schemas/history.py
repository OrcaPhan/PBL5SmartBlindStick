"""
Schema định nghĩa dữ liệu trả về cho phần Lịch sử (History).
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


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

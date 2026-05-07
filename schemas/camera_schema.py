"""
Schemas cho luồng camera upload ảnh nhận diện.
"""

from pydantic import BaseModel


class CameraUploadOut(BaseModel):
    """Schema response cho API upload ảnh từ ESP32-CAM."""

    message: str
    class_name: str
    confidence: float
    image_url: str | None = None

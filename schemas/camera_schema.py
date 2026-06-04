"""
Schemas cho luồng camera upload ảnh nhận diện.
"""

from pydantic import BaseModel, field_validator


class CameraUploadOut(BaseModel):
    """Schema response cho API upload ảnh từ ESP32-CAM."""

    message: str
    class_name: str
    confidence: float
    image_url: str | None = None

    @field_validator("image_url", mode="after")
    @classmethod
    def format_image_url(cls, v: str | None) -> str | None:
        if not v:
            return v
        from core.minio_client import minio_client
        return minio_client.get_full_url(v)


class CameraToggleIn(BaseModel):
    """Schema cho API bật/tắt camera từ web."""
    
    stick_id: str
    action: str  # "on" hoặc "off"

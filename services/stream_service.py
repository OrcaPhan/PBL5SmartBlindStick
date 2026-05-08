"""
Service lưu frame mới nhất từ ESP32-CAM và phát MJPEG stream cho client.
"""

from __future__ import annotations

import asyncio
import time
from typing import AsyncGenerator

# Lưu frame mới nhất cho từng stick_id
# Format: { "stick_id": {"bytes": b"...", "timestamp": 1234567890.123} }
_latest_frames: dict[str, dict] = {}


def update_frame(stick_id: str, frame_bytes: bytes) -> None:
    """
    Cập nhật frame mới nhất nhận được từ ESP32-CAM cho một stick.
    Được gọi mỗi khi có ảnh upload lên POST /api/camera/upload.
    """
    _latest_frames[stick_id] = {
        "bytes": frame_bytes,
        "timestamp": time.monotonic(),
    }


async def frame_generator(stick_id: str) -> AsyncGenerator[bytes, None]:
    """
    Async generator trả về liên tục các frame mới nhất theo chuẩn MJPEG.
    Client (browser, app) mở kết nối GET /api/camera/stream/{stick_id}
    và nhận từng frame khi có frame mới.
    FPS thực tế phụ thuộc vào tốc độ upload của ESP32-CAM (không bị thay đổi).
    """
    last_timestamp: float = -1.0

    while True:
        frame_data = _latest_frames.get(stick_id)

        if frame_data is not None and frame_data["timestamp"] > last_timestamp:
            last_timestamp = frame_data["timestamp"]
            frame_bytes: bytes = frame_data["bytes"]

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + frame_bytes
                + b"\r\n"
            )
        else:
            # Chưa có frame mới -> đợi ngắn để không chiếm CPU
            # Vòng lặp poll ở 50ms (~20 lần/giây) nhưng chỉ yield khi có frame thực sự mới
            await asyncio.sleep(0.05)

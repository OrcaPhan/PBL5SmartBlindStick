"""
Service xử lý ảnh camera: nhận diện, gửi cảnh báo và lưu log.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from core.ai_model import ai_model
from core.minio_client import minio_client
from core.mqtt_client import mqtt_client
from repositories.detection_repo import insert_detection_log

CONFIDENCE_THRESHOLD = 30.0
SPAM_GAP_SECONDS = 3
ALERT_TOPIC_TEMPLATE = "pbl5/smart_cane/{stick_id}/command"

_last_detection_by_stick: dict[str, dict[str, str | datetime]] = {}
logger = logging.getLogger(__name__)


def _build_image_object_name(stick_id: str) -> str:
    """Tạo object path theo format images/{device_id}/{date}/{hour}/{timestamp}.jpg."""
    now = datetime.now()
    date_part = now.strftime("%Y-%m-%d")
    hour_part = now.strftime("%H")
    timestamp_part = now.strftime("%Y%m%d_%H%M%S_%f")
    unique_suffix = uuid4().hex[:8]
    return f"images/{stick_id}/{date_part}/{hour_part}/{timestamp_part}_{unique_suffix}.jpg"


def _should_send_alert(stick_id: str, object_name: str, now: datetime) -> bool:
    """Kiểm tra chống spam dựa trên object trước đó và thời gian 3 giây."""
    last_data = _last_detection_by_stick.get(stick_id)
    if not last_data:
        return True

    last_object = str(last_data.get("object_name", ""))
    last_time = last_data.get("detected_at")
    if not isinstance(last_time, datetime):
        return True

    if object_name != last_object:
        return True

    return (now - last_time) > timedelta(seconds=SPAM_GAP_SECONDS)


def _build_alert_topic(stick_id: str) -> str:
    """Tạo topic MQTT riêng cho từng gậy để tránh gửi nhầm thiết bị."""
    return ALERT_TOPIC_TEMPLATE.format(stick_id=stick_id)


def _map_class_to_audio_file(class_index: int) -> int:
    """
    Map class_index từ AI sang số file MP3.
    Mặc định dùng index + 1 để khớp cách đánh số file của DFPlayer (001, 002...).
    """
    return max(1, class_index + 1)


async def process_camera_frame(
    db: AsyncSession,
    image_bytes: bytes,
    stick_id: str,
) -> dict[str, str | float]:
    """
    Xử lý 1 frame ảnh từ ESP32-CAM theo luồng:
    AI nhận diện -> MQTT -> MinIO -> DB (khi vượt ngưỡng confidence).
    """
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Anh dau vao khong hop le.",
        )
    if not stick_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="stick_id khong duoc de trong.",
        )

    try:
        class_name, confidence, class_index = ai_model.predict(image_bytes)
    except Exception as exc:
        logger.exception("Loi suy luan AI khi xu ly anh camera.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the suy luan AI tu anh camera.",
        ) from exc

    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "message": "No obstacle detected",
            "class_name": class_name,
            "confidence": confidence,
        }

    now = datetime.now()
    if not _should_send_alert(stick_id=stick_id, object_name=class_name, now=now):
        return {
            "message": "Obstacle skipped due to anti-spam",
            "class_name": class_name,
            "confidence": confidence,
        }

    try:
        # Bước 1: Gửi MQTT trước để cảnh báo ngay lập tức.
        alert_topic = _build_alert_topic(stick_id=stick_id)
        file_number = _map_class_to_audio_file(class_index=class_index)
        mqtt_client.publish_command(
            topic=alert_topic,
            message=str(file_number),
        )

        # Bước 2: Upload MinIO, lấy URL public của ảnh.
        file_name = _build_image_object_name(stick_id=stick_id)
        image_url = minio_client.upload_image(file_bytes=image_bytes, file_name=file_name)

        # Bước 3: Lưu DB với image_url vừa tạo.
        await insert_detection_log(
            db=db,
            stick_id=stick_id,
            object_name=class_name,
            confidence=confidence,
            image_url=image_url,
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.exception("Loi SQLAlchemy khi luu detection log.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Loi he thong khi luu detection log.",
        ) from exc
    except Exception as exc:
        logger.exception("Loi tong quat trong luong xu ly frame camera.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the xu ly frame camera.",
        ) from exc

    _last_detection_by_stick[stick_id] = {
        "object_name": class_name,
        "detected_at": now,
    }

    return {
        "message": "Obstacle detected and processed",
        "class_name": class_name,
        "confidence": confidence,
        "image_url": image_url,
    }

"""
Repository thao tác dữ liệu detection_logs.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from models.detection_log import DetectionLog


async def insert_detection_log(
    db: AsyncSession,
    stick_id: str,
    object_name: str,
    confidence: float,
    image_url: str,
) -> DetectionLog:
    """
    Ghi một bản ghi nhận diện vật cản vào bảng detection_logs.
    """
    detection_log = DetectionLog(
        stick_id=stick_id,
        object_name=object_name,
        confidence=confidence,
        image_url=image_url,
    )
    db.add(detection_log)
    await db.commit()
    await db.refresh(detection_log)
    return detection_log

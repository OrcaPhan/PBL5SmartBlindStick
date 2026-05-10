"""
Repository thao tác dữ liệu lịch sử (History).
"""

from datetime import date
from typing import List

from sqlalchemy import func, extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.detection_log import DetectionLog


async def get_history_summary(db: AsyncSession, stick_id: str, target_date: date) -> dict:
    """
    Lấy thông tin tổng quan của lịch sử phát hiện vật cản trong một ngày.
    Trả về: số lượng ảnh, tổng số khung giờ có dữ liệu, độ tin cậy trung bình, danh sách các giờ (desc).
    """
    # 1. Lấy tổng ảnh và trung bình confidence
    stmt_stats = (
        select(
            func.count(DetectionLog.id).label("total_images"),
            func.avg(DetectionLog.confidence).label("avg_confidence")
        )
        .where(
            DetectionLog.stick_id == stick_id,
            func.date(DetectionLog.timestamp) == target_date
        )
    )
    result_stats = await db.execute(stmt_stats)
    stats = result_stats.first()
    
    total_images = stats.total_images or 0
    # Xử lý avg_confidence nếu None thì về 0.0
    avg_confidence = round(stats.avg_confidence, 2) if stats.avg_confidence is not None else 0.0

    # 2. Lấy danh sách các khung giờ có dữ liệu (sắp xếp giảm dần)
    stmt_hours = (
        select(extract('hour', DetectionLog.timestamp).label("hour"))
        .where(
            DetectionLog.stick_id == stick_id,
            func.date(DetectionLog.timestamp) == target_date
        )
        .group_by(extract('hour', DetectionLog.timestamp))
        .order_by(extract('hour', DetectionLog.timestamp).desc())
    )
    result_hours = await db.execute(stmt_hours)
    hours = [int(row.hour) for row in result_hours.fetchall()]

    return {
        "total_images": total_images,
        "total_timeframes": len(hours),
        "average_confidence": avg_confidence,
        "available_hours": hours
    }


async def get_detections_by_hour(
    db: AsyncSession, stick_id: str, target_date: date, hour: int
) -> List[DetectionLog]:
    """
    Lấy chi tiết danh sách ảnh và log nhận diện trong một khung giờ cụ thể.
    """
    stmt = (
        select(DetectionLog)
        .where(
            DetectionLog.stick_id == stick_id,
            func.date(DetectionLog.timestamp) == target_date,
            extract('hour', DetectionLog.timestamp) == hour
        )
        .order_by(DetectionLog.timestamp.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())

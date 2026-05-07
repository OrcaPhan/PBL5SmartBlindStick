"""
Router cho API camera upload ảnh từ ESP32-CAM.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.camera_schema import CameraUploadOut
from services.ai_service import process_camera_frame

router = APIRouter(prefix="/api/camera", tags=["Camera"])


@router.post(
    "/upload",
    response_model=CameraUploadOut,
    status_code=status.HTTP_200_OK,
)
async def upload_camera_image(
    file: UploadFile = File(...),
    stick_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> CameraUploadOut:
    """
    Nhận ảnh từ ESP32-CAM và xử lý nhận diện vật cản.
    """
    try:
        image_bytes = await file.read()
        result = await process_camera_frame(
            db=db,
            image_bytes=image_bytes,
            stick_id=stick_id,
        )
        return CameraUploadOut(**result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the xu ly upload anh tu camera.",
        ) from exc

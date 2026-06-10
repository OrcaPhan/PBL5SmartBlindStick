"""
Router cho API camera upload ảnh từ ESP32-CAM.
"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.camera_schema import CameraUploadOut, CameraToggleIn
from services.ai_service import get_latest_ai_result, process_camera_frame
from services.stream_service import frame_generator, update_frame
from core.mqtt_client import mqtt_client
from core.security import get_current_user
from models.user import User

router = APIRouter(prefix="/api/camera", tags=["Camera"])


@router.post(
    "/upload",
    response_model=CameraUploadOut,
    status_code=status.HTTP_200_OK,
)
async def upload_camera_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    stick_id: str = Form(...),
) -> CameraUploadOut:
    """
    Nhận ảnh từ ESP32-CAM và xử lý nhận diện vật cản.
    """
    try:
        image_bytes = await file.read()

        # Cập nhật bộ đệm stream để phục vụ GET /stream/{stick_id}
        update_frame(stick_id, image_bytes)

        result = await process_camera_frame(
            image_bytes=image_bytes,
            stick_id=stick_id,
            background_tasks=background_tasks,
        )
        return CameraUploadOut(**result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Khong the xu ly upload anh tu camera.",
        ) from exc


@router.get(
    "/stream/{stick_id}",
    summary="MJPEG live stream từ ESP32-CAM",
    tags=["Camera"],
)
async def stream_camera(stick_id: str) -> StreamingResponse:
    """
    Trả về luồng MJPEG liên tục (multipart/x-mixed-replace).
    Mở trong browser hoặc thẻ <img src=".../stream/{stick_id}"> trên frontend.
    FPS phụ thuộc vào tốc độ upload thực tế của ESP32-CAM.
    """
    return StreamingResponse(
        frame_generator(stick_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@router.post(
    "/toggle",
    summary="Bật/Tắt luồng stream camera từ Web",
    tags=["Camera"],
)
async def toggle_camera(
    payload: CameraToggleIn,
    current_user: User = Depends(get_current_user),
):
    """
    Gửi tín hiệu MQTT về phần cứng (ESP32) để bắt đầu hoặc ngừng việc gửi ảnh lên Server.
    - action = "on": ESP32-CAM bắt đầu bật camera và liên tục upload ảnh lên `/upload`.
    - action = "off": ESP32-CAM tắt camera để tiết kiệm pin/băng thông.
    """
    topic = f"pbl5/smart_cane/{payload.stick_id}/command"
    command = "CAM_ON" if payload.action == "on" else "CAM_OFF"
    
    try:
        mqtt_client.publish_command(topic=topic, message=command)
        return {"message": f"Đã gửi lệnh {command} tới gậy {payload.stick_id} thành công."}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi gửi lệnh điều khiển camera: {str(exc)}"
        )


@router.get(
    "/latest-result/{stick_id}",
    summary="Lấy kết quả nhận diện AI mới nhất",
    tags=["Camera"],
)
async def get_latest_result(stick_id: str):
    """
    Trả về kết quả nhận diện AI mới nhất (real-time) của gậy.
    Dùng cho Frontend polling (gọi định kỳ mỗi 1s - 2s) để hiển thị thông tin cảnh báo.
    """
    result = get_latest_ai_result(stick_id)
    if not result:
        return {"status": "waiting", "message": "Chưa có dữ liệu nhận diện"}
    
    return {"status": "success", "data": result}

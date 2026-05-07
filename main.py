"""
Điểm khởi chạy chính của ứng dụng FastAPI.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers.auth_router import router as auth_router
from controllers.camera_router import router as camera_router
from controllers.hardware_router import router as hardware_router
from core.ai_model import preload_ai_model
from core.database import close_db, init_db
from core.mqtt_client import mqtt_client

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Smart Stick Backend",
    description="Backend cho hệ thống Gậy Thông Minh (IoT + AI).",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(hardware_router)
app.include_router(camera_router)


@app.on_event("startup")
async def on_startup() -> None:
    """Khởi tạo tài nguyên hệ thống khi ứng dụng start."""
    await init_db()
    preload_ai_model()
    try:
        mqtt_client.connect()
    except Exception:
        # Cho phep backend van khoi dong (dev auth/API) neu mang truong chan DNS/MQTT.
        logger.warning(
            "Khong the ket noi MQTT broker luc startup. Backend van tiep tuc chay.",
            exc_info=True,
        )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Đóng tài nguyên hệ thống khi ứng dụng shutdown."""
    await close_db()
    mqtt_client.disconnect()


@app.get("/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """API kiểm tra trạng thái hoạt động của server."""
    return {"status": "ok"}

"""
MQTT client: publish lệnh xuống thiết bị VÀ subscribe nhận dữ liệu từ thiết bị.

Quy hoạch topic (pbl5/smart_cane/{stick_id}/<chức_năng>):

  [ESP32 → Server] PUBLISH:
    pbl5/smart_cane/{id}/gps      → dữ liệu GPS + pin
    pbl5/smart_cane/{id}/status   → trạng thái online/offline (retained)

  [Server → ESP32] PUBLISH:
    pbl5/smart_cane/{id}/command  → số file MP3 cần phát
    pbl5/smart_cane/{id}/alert    → chuỗi cảnh báo khẩn từ caretaker
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Pattern topic nhận từ thiết bị ──────────────────────────────────────────
TOPIC_GPS_WILDCARD    = "pbl5/smart_cane/+/gps"
TOPIC_STATUS_WILDCARD = "pbl5/smart_cane/+/status"
TOPIC_IMU_WILDCARD    = "pbl5/smart_cane/+/imu"


def _build_topic(stick_id: str, channel: str) -> str:
    return f"pbl5/smart_cane/{stick_id}/{channel}"


class MqttClient:
    """MQTT Client cho backend: subscribe GPS + publish command/alert."""

    def __init__(self) -> None:
        self.broker_host = os.getenv("MQTT_BROKER_HOST", "broker.hivemq.com")
        self.broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        self.keepalive   = int(os.getenv("MQTT_KEEPALIVE", "60"))
        self.client_id   = os.getenv("MQTT_CLIENT_ID", "pbl5-fastapi-server")

        self._client    = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)
        self._connected = False

        # asyncio event loop để chạy coroutine từ thread paho
        self._loop: asyncio.AbstractEventLoop | None = None

        self._client.on_connect    = self._on_connect
        self._client.on_message    = self._on_message
        self._client.on_disconnect = self._on_disconnect

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def connect(self) -> None:
        """Kết nối broker + bắt đầu background thread."""
        if self._connected:
            return
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = None

        self._client.connect(self.broker_host, self.broker_port, self.keepalive)
        self._client.loop_start()
        self._connected = True
        logger.info("[MQTT] Dang ket noi toi broker %s:%s", self.broker_host, self.broker_port)

    def disconnect(self) -> None:
        """Ngắt kết nối an toàn."""
        if not self._connected:
            return
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False
        logger.info("[MQTT] Da ngat ket noi broker.")

    # ── Internal callbacks ───────────────────────────────────────────────────

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: dict, rc: int) -> None:
        if rc == 0:
            logger.info("[MQTT] Ket noi broker thanh cong.")
            # Subscribe nhận dữ liệu từ tất cả thiết bị
            client.subscribe(TOPIC_GPS_WILDCARD,    qos=0)
            client.subscribe(TOPIC_STATUS_WILDCARD, qos=0)
            client.subscribe(TOPIC_IMU_WILDCARD,    qos=0)
            logger.info("[MQTT] Subscribed: %s", TOPIC_GPS_WILDCARD)
            logger.info("[MQTT] Subscribed: %s", TOPIC_STATUS_WILDCARD)
            logger.info("[MQTT] Subscribed: %s", TOPIC_IMU_WILDCARD)
        else:
            logger.error("[MQTT] Ket noi that bai, rc=%s", rc)

    def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
        self._connected = False
        logger.warning("[MQTT] Mat ket noi broker (rc=%s). Se tu dong ket noi lai.", rc)

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        """Xử lý message nhận được từ thiết bị."""
        topic   = msg.topic
        payload = msg.payload.decode("utf-8", errors="ignore")
        logger.info("[MQTT] Nhan '%s': %s", topic, payload)

        # ── Xử lý GPS ────────────────────────────────────────────────────────
        if topic.endswith("/gps"):
            self._handle_gps(payload)

        # ── Xử lý Status ─────────────────────────────────────────────────────
        elif topic.endswith("/status"):
            self._handle_status(payload)

        # ── Xử lý IMU ────────────────────────────────────────────────────────
        elif topic.endswith("/imu"):
            self._handle_imu(payload)

    def _handle_gps(self, payload: str) -> None:
        """Lưu GPS vào DB và broadcast WebSocket."""
        try:
            data = json.loads(payload)
            stick_id = data.get("stick_id")
            lat      = data.get("lat")
            lon      = data.get("lon")
            battery  = data.get("battery", 100)

            if not all([stick_id, lat is not None, lon is not None]):
                logger.warning("[MQTT/GPS] Payload thieu truong: %s", data)
                return

            # Chạy coroutine lưu DB trong asyncio event loop của FastAPI
            if self._loop and not self._loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self._save_gps_async(stick_id, lat, lon, battery),
                    self._loop,
                )
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("[MQTT/GPS] Parse payload that bai: %s | %s", payload, exc)

    def _handle_status(self, payload: str) -> None:
        """Log trạng thái online/offline của thiết bị."""
        try:
            data   = json.loads(payload)
            stick  = data.get("stick_id", "unknown")
            status = data.get("status", "unknown")
            logger.info("[MQTT/Status] Thiet bi '%s' -> %s", stick, status)
        except json.JSONDecodeError:
            logger.warning("[MQTT/Status] Payload khong hop le: %s", payload)

    async def _save_gps_async(self, stick_id: str, lat: float, lon: float, battery: int) -> None:
        """Lưu tọa độ vào DB và push WebSocket."""
        from core.database import async_session_factory as AsyncSessionLocal
        from core.websocket_manager import ws_manager
        from repositories.hardware_repo import insert_location_history
        from schemas.hardware_schema import HardwareGpsIn

        async with AsyncSessionLocal() as db:
            payload_schema = HardwareGpsIn(
                stick_id=stick_id, lat=lat, lon=lon, battery=battery
            )
            location = await insert_location_history(db=db, payload=payload_schema)
            logger.info("[MQTT/GPS] Da luu vao DB: id=%s stick=%s lat=%s lon=%s",
                        location.id, stick_id, lat, lon)

            # Broadcast WebSocket cho Frontend
            await ws_manager.broadcast_location(stick_id, {
                "id":       location.id,
                "stick_id": stick_id,
                "lat":      lat,
                "lon":      lon,
                "battery":  battery,
                "timestamp": str(location.timestamp),
            })

    def _handle_imu(self, payload: str) -> None:
        """Lưu dữ liệu IMU (gia tốc/góc nghiêng) vào DB."""
        try:
            data = json.loads(payload)
            stick_id = data.get("stick_id")
            acc_x    = data.get("acc_x")
            acc_y    = data.get("acc_y")
            acc_z    = data.get("acc_z")
            gyro_x   = data.get("gyro_x")
            gyro_y   = data.get("gyro_y")
            gyro_z   = data.get("gyro_z")

            if not all([stick_id, acc_x is not None, acc_y is not None, acc_z is not None,
                        gyro_x is not None, gyro_y is not None, gyro_z is not None]):
                logger.warning("[MQTT/IMU] Payload thieu truong: %s", data)
                return

            if self._loop and not self._loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self._save_imu_async(
                        stick_id=stick_id,
                        acc_x=float(acc_x), acc_y=float(acc_y), acc_z=float(acc_z),
                        gyro_x=float(gyro_x), gyro_y=float(gyro_y), gyro_z=float(gyro_z)
                    ),
                    self._loop,
                )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.error("[MQTT/IMU] Parse payload that bai: %s | %s", payload, exc)

    async def _save_imu_async(
        self, stick_id: str,
        acc_x: float, acc_y: float, acc_z: float,
        gyro_x: float, gyro_y: float, gyro_z: float
    ) -> None:
        """Lưu các chỉ số IMU vào DB và kích hoạt xử lý nghiệp vụ."""
        from core.database import async_session_factory as AsyncSessionLocal
        from repositories.hardware_repo import insert_imu_log
        from schemas.hardware_schema import HardwareImuIn
        from services.imu_service import process_new_imu_data

        async with AsyncSessionLocal() as db:
            payload_schema = HardwareImuIn(
                stick_id=stick_id,
                acc_x=acc_x, acc_y=acc_y, acc_z=acc_z,
                gyro_x=gyro_x, gyro_y=gyro_y, gyro_z=gyro_z
            )
            imu_log = await insert_imu_log(db=db, payload=payload_schema)
            logger.info("[MQTT/IMU] Da luu vao DB: id=%s stick=%s acc=(%s,%s,%s) gyro=(%s,%s,%s)",
                        imu_log.id, stick_id, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z)

            # Kích hoạt xử lý phân tích ngã & hoạt động
            await process_new_imu_data(db=db, stick_id=stick_id, new_log=imu_log)

    # ── Publish helpers ──────────────────────────────────────────────────────

    def publish_command(self, topic: str, message: dict[str, Any] | str) -> None:
        """Publish một message tuỳ ý lên topic."""
        if not topic:
            raise ValueError("Topic MQTT khong duoc de trong.")
        payload = json.dumps(message, ensure_ascii=False) if isinstance(message, dict) else message
        self.connect()
        result = self._client.publish(topic, payload=payload, qos=0, retain=False)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Khong the publish len topic '{topic}'. rc={result.rc}")

    def publish_audio_command(self, stick_id: str, file_number: int) -> None:
        """Gửi lệnh phát âm thanh xuống thiết bị."""
        topic = _build_topic(stick_id, "command")
        self.publish_command(topic, str(file_number))
        logger.info("[MQTT] Gui lenh audio file=%s toi '%s'", file_number, stick_id)

    def publish_alert(self, stick_id: str, message: str) -> None:
        """Gửi cảnh báo khẩn cấp xuống thiết bị."""
        topic = _build_topic(stick_id, "alert")
        self.publish_command(topic, message)
        logger.info("[MQTT] Gui canh bao toi '%s': %s", stick_id, message)


mqtt_client = MqttClient()


def publish_command(topic: str, message: dict[str, Any] | str) -> None:
    """Hàm tiện ích tương thích ngược."""
    mqtt_client.publish_command(topic=topic, message=message)

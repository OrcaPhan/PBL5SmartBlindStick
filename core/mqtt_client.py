"""
Cấu hình MQTT client dùng để gửi lệnh tới thiết bị.
"""

from __future__ import annotations

import json
import os
from typing import Any
from dotenv import load_dotenv

import paho.mqtt.client as mqtt

load_dotenv()


class MqttClient:
    """Wrapper MQTT để tái sử dụng publish command trong toàn hệ thống."""

    def __init__(self) -> None:
        self.broker_host = os.getenv("MQTT_BROKER_HOST", "broker.hivemq.com")
        self.broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
        self.keepalive = int(os.getenv("MQTT_KEEPALIVE", "60"))
        self.client_id = os.getenv("MQTT_CLIENT_ID", "smart-stick-fastapi")

        self._client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv311)
        self._connected = False

    def connect(self) -> None:
        """Kết nối broker nếu chưa kết nối."""
        if self._connected:
            return
        self._client.connect(self.broker_host, self.broker_port, self.keepalive)
        self._client.loop_start()
        self._connected = True

    def disconnect(self) -> None:
        """Ngắt kết nối broker an toàn."""
        if not self._connected:
            return
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False

    def publish_command(self, topic: str, message: dict[str, Any] | str) -> None:
        """
        Publish command lên một topic MQTT.
        - `topic`: topic đích.
        - `message`: dict hoặc string.
        """
        if not topic:
            raise ValueError("Topic MQTT khong duoc de trong.")

        payload = json.dumps(message, ensure_ascii=False) if isinstance(message, dict) else message
        self.connect()
        result = self._client.publish(topic, payload=payload, qos=0, retain=False)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Khong the publish command len topic '{topic}'. rc={result.rc}")


mqtt_client = MqttClient()


def publish_command(topic: str, message: dict[str, Any] | str) -> None:
    """Hàm tiện ích dùng lại ở service/controller."""
    mqtt_client.publish_command(topic=topic, message=message)

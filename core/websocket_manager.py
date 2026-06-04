"""
Quản lý các kết nối WebSocket cho thời gian thực.
"""

import json
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        # Lưu các kết nối theo stick_id: { "STK001": [ws1, ws2, ...] }
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, stick_id: str):
        await websocket.accept()
        if stick_id not in self.active_connections:
            self.active_connections[stick_id] = []
        self.active_connections[stick_id].append(websocket)

    def disconnect(self, websocket: WebSocket, stick_id: str):
        if stick_id in self.active_connections:
            if websocket in self.active_connections[stick_id]:
                self.active_connections[stick_id].remove(websocket)
            if not self.active_connections[stick_id]:
                del self.active_connections[stick_id]

    async def broadcast_location(self, stick_id: str, location_data: dict):
        if stick_id in self.active_connections:
            message = json.dumps(location_data, default=str)
            # Send the message to all active clients listening to this stick_id
            for connection in self.active_connections[stick_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass

    async def broadcast_alert(self, stick_id: str, alert_data: dict):
        """Phát tín hiệu cảnh báo/cập nhật hoạt động qua WebSocket."""
        if stick_id in self.active_connections:
            message = json.dumps(alert_data, default=str)
            for connection in self.active_connections[stick_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass

ws_manager = WebSocketManager()

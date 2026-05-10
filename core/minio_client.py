"""
Client MinIO phục vụ lưu trữ ảnh nhận diện từ ESP32-CAM.
"""

from __future__ import annotations

import io
import json
import os
from dotenv import load_dotenv

from minio import Minio
from minio.error import S3Error

load_dotenv()


class MinioClient:
    """Wrapper thao tác MinIO để upload ảnh và trả URL public."""

    def __init__(self) -> None:
        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000").strip()
        self.access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin").strip()
        self.secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin").strip()
        self.secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
        self.public_endpoint = os.getenv("MINIO_PUBLIC_ENDPOINT", self.endpoint).strip()
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "smart-stick").strip()

        if not self.endpoint or not self.access_key or not self.secret_key:
            raise ValueError(
                "Thieu cau hinh MinIO. Vui long set MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY."
            )

        self.client = Minio(
            endpoint=self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure,
        )

    def _ensure_bucket_exists(self) -> None:
        """Đảm bảo bucket tồn tại trước khi upload ảnh."""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
            # Đặt policy public read để object có thể truy cập trực tiếp qua URL.
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": ["*"]},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"],
                    }
                ],
            }
            self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))
        except S3Error as exc:
            raise RuntimeError(f"Khong the kiem tra/tao bucket '{self.bucket_name}': {exc}") from exc

    def upload_image(self, file_bytes: bytes, file_name: str) -> str:
        """
        Upload ảnh vào bucket MinIO và trả về URL public của ảnh.

        Args:
            file_bytes: Nội dung ảnh dạng bytes.
            file_name: Tên file lưu trên bucket.
        """
        if not file_bytes:
            raise ValueError("Noi dung file khong hop le.")
        if not file_name:
            raise ValueError("Ten file khong duoc de trong.")

        self._ensure_bucket_exists()

        file_stream = io.BytesIO(file_bytes)
        file_size = len(file_bytes)

        content_type = "image/jpeg"
        lower_name = file_name.lower()
        if lower_name.endswith(".png"):
            content_type = "image/png"
        elif lower_name.endswith(".webp"):
            content_type = "image/webp"

        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_name,
                data=file_stream,
                length=file_size,
                content_type=content_type,
            )
        except S3Error as exc:
            raise RuntimeError(f"Khong the upload anh '{file_name}' len MinIO: {exc}") from exc

        scheme = "https" if self.secure else "http"
        endpoint = self.public_endpoint
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            base_url = endpoint.rstrip("/")
        else:
            base_url = f"{scheme}://{endpoint.rstrip('/')}"

        return f"{base_url}/{self.bucket_name}/{file_name}"


minio_client = MinioClient()

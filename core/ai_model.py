"""
Khởi tạo AI model MobileNetV3 theo mô hình singleton.
Dành cho Server phân tích hình ảnh từ ESP32-CAM.
"""

from __future__ import annotations

import os
from pathlib import Path
import io

import torch
from PIL import Image
from torch import nn
from torchvision import transforms


# Đã cập nhật tên file trọng số mặc định khớp với tên file xuất ra từ Kaggle
MODEL_PATH = os.getenv("AI_MODEL_PATH", "weights/mobilenetv3_obstacle_best_2.pth")
MODEL_NAME = os.getenv("AI_MODEL_NAME", "mobilenet_v3_large")
NUM_CLASSES = int(os.getenv("AI_NUM_CLASSES", "10"))
IMAGE_SIZE = int(os.getenv("AI_IMAGE_SIZE", "224"))

# =================================================================
# DANH SÁCH LỚP CHUẨN XÁC (Khớp 100% với thứ tự Alphabet lúc train)
# 0: chair | 1: door | 2: fence | 3: garbage_bin | 4: obstacle
# 5: plant | 6: pothole | 7: stairs | 8: table | 9: vehicle
# =================================================================
CLASS_NAMES = [name.strip() for name in os.getenv("AI_CLASS_NAMES", "").split(",") if name.strip()]
if not CLASS_NAMES:
    CLASS_NAMES = [
        "Ghe",         # 0: chair
        "Cua",         # 1: door
        "Hang rao",    # 2: fence
        "Thung rac",   # 3: garbage_bin
        "Vat can",     # 4: obstacle
        "Cay coi",     # 5: plant
        "O ga",        # 6: pothole
        "Cau thang",   # 7: stairs
        "Ban",         # 8: table
        "Xe co",       # 9: vehicle
    ]

# Danh sách gốc tương ứng với thứ tự file âm thanh MP3 trên thẻ nhớ của gậy
ORIGINAL_CLASS_NAMES = [
    "Ghe",        # 0001.mp3
    "Cua",        # 0002.mp3
    "Hang rao",   # 0003.mp3
    "Thung rac",  # 0004.mp3
    "Vat can",    # 0005.mp3
    "Cay coi",    # 0006.mp3
    "O ga",       # 0007.mp3 
    "Cau thang",  # 0008.mp3
    "Ban",        # 0009.mp3
    "Xe co",      # 0010.mp3
    "Nguoi",      # 0011.mp3
]


class AiModelSingleton:
    """
    Singleton quản lý model + transforms.
    Đảm bảo model chỉ load 1 lần vào RAM/VRAM khi startup.
    """

    _instance: "AiModelSingleton | None" = None

    def __new__(cls) -> "AiModelSingleton":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._is_initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._is_initialized:
            return
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model: nn.Module | None = None
        self.transform = transforms.Compose(
            [
                transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )
        self._is_initialized = True

    def load(self) -> None:
        """Load model vào bộ nhớ, chỉ thực hiện một lần."""
        if self.model is not None:
            return

        # Cập nhật kiến trúc khởi tạo cho MobileNetV3
        if MODEL_NAME == "mobilenet_v3_large":
            import torchvision.models as models
            # Khởi tạo khung model MobileNetV3 với số lớp tùy chỉnh
            model = models.mobilenet_v3_large(num_classes=NUM_CLASSES)
        elif MODEL_NAME == "mobilenet_v2":
            import torchvision.models as models
            model = models.mobilenet_v2(num_classes=NUM_CLASSES)
        else:
            import timm
            model = timm.create_model(
                MODEL_NAME,
                pretrained=False,
                num_classes=NUM_CLASSES,
            )

        weight_path = Path(MODEL_PATH)
        if not weight_path.exists():
            raise FileNotFoundError(f"Khong tim thay file weight: {weight_path}")

        # Tải trọng số
        state_dict = torch.load(weight_path, map_location=self.device, weights_only=False)
        try:
            model.load_state_dict(state_dict)
        except RuntimeError as exc:
            raise RuntimeError(
                f"Khong load duoc weight AI. Kiem tra AI_MODEL_NAME={MODEL_NAME} co khop kien truc file weight hay khong."
            ) from exc
            
        model.to(self.device)
        model.eval()
        self.model = model

    def _predict_logits(self, image: Image.Image) -> torch.Tensor:
        """
        Chạy suy luận cho 1 ảnh PIL.
        Trả về logits tensor.
        """
        if self.model is None:
            self.load()

        assert self.model is not None  # giúp type checker
        with torch.inference_mode():
            # Đưa ảnh qua transform và chuyển lên thiết bị (CPU/GPU)
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            
            # Sử dụng autocast để tăng tốc nếu đang chạy trên GPU
            if self.device.type == 'cuda':
                with torch.amp.autocast('cuda'):
                    logits = self.model(image_tensor)
            else:
                logits = self.model(image_tensor)
                
            return logits

    def predict(self, image_bytes: bytes) -> tuple[str, float, int]:
        """
        Chạy suy luận từ bytes ảnh gửi từ ESP32.
        Trả về (class_name, confidence_percent, class_index).
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        logits = self._predict_logits(image)
        probs = torch.softmax(logits, dim=1)
        
        confidence, class_index_tensor = torch.max(probs, dim=1)
        model_index = int(class_index_tensor.item())
        confidence_percent = float(confidence.item() * 100)

        # 1. Lấy tên tiếng Việt từ danh sách chuẩn khớp với model
        if 0 <= model_index < len(CLASS_NAMES):
            class_name = CLASS_NAMES[model_index]
        else:
            class_name = f"class_{model_index}"

        # 2. Ánh xạ ngược về chỉ số index cũ để mạch ESP32 phát đúng MP3
        try:
            class_index = ORIGINAL_CLASS_NAMES.index(class_name)
        except ValueError:
            class_index = model_index

        return class_name, confidence_percent, class_index


ai_model = AiModelSingleton()


def preload_ai_model() -> None:
    """Hàm gọi lúc startup server (ví dụ: FastAPI startup event) để đưa model lên RAM."""
    ai_model.load()
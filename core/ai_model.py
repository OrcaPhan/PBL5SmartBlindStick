"""
Khởi tạo AI model ViT DINOv2 theo mô hình singleton.
"""

from __future__ import annotations

import os
from pathlib import Path
import io

import timm
import torch
from PIL import Image
from torch import nn
from torchvision import transforms


MODEL_PATH = os.getenv("AI_MODEL_PATH", "weights/AI-PBL5-PHANLOAI.pth")
MODEL_NAME = os.getenv("AI_MODEL_NAME", "vit_base_patch14_dinov2.lvd142m")
NUM_CLASSES = int(os.getenv("AI_NUM_CLASSES", "11"))
IMAGE_SIZE = int(os.getenv("AI_IMAGE_SIZE", "518"))
CLASS_NAMES = [name.strip() for name in os.getenv("AI_CLASS_NAMES", "").split(",") if name.strip()]
if not CLASS_NAMES:
    CLASS_NAMES = [
        "Ghe",
        "Cua",
        "Hang rao",
        "Thung rac",
        "Vat can",
        "Cay coi",
        "O ga",
        "Cau thang",
        "Ban",
        "Xe co",
        "Nguoi",
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

        model = timm.create_model(
            MODEL_NAME,
            pretrained=False,
            num_classes=NUM_CLASSES,
        )

        weight_path = Path(MODEL_PATH)
        if not weight_path.exists():
            raise FileNotFoundError(f"Khong tim thay file weight: {weight_path}")

        state_dict = torch.load(weight_path, map_location=self.device)
        try:
            model.load_state_dict(state_dict)
        except RuntimeError as exc:
            raise RuntimeError(
                "Khong load duoc weight AI. Kiem tra AI_MODEL_NAME co khop kien truc file weight hay khong."
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
            image_tensor = self.transform(image).unsqueeze(0).to(self.device)
            logits = self.model(image_tensor)
            return logits

    def predict(self, image_bytes: bytes) -> tuple[str, float, int]:
        """
        Chạy suy luận từ bytes ảnh.
        Trả về (class_name, confidence_percent, class_index).
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        logits = self._predict_logits(image)
        probs = torch.softmax(logits, dim=1)
        confidence, class_index_tensor = torch.max(probs, dim=1)
        class_index = int(class_index_tensor.item())
        confidence_percent = float(confidence.item() * 100)

        if 0 <= class_index < len(CLASS_NAMES):
            class_name = CLASS_NAMES[class_index]
        else:
            class_name = f"class_{class_index}"

        return class_name, confidence_percent, class_index


ai_model = AiModelSingleton()


def preload_ai_model() -> None:
    """Hàm gọi lúc startup để preload model."""
    ai_model.load()

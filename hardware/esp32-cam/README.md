# ESP32-CAM uploader

Code mau de ESP32-CAM gui anh len API `POST /api/camera/upload` cua FastAPI backend.

## 1) Sua cau hinh trong `esp32_cam_uploader.ino`

- `WIFI_SSID`, `WIFI_PASSWORD`
- `SERVER_HOST`: IP may tinh chay FastAPI (vi du `192.168.1.100`)
- `SERVER_PORT`: mac dinh `8000`
- `SERVER_PATH`: `/api/camera/upload`
- `STICK_ID`: ma gay (vi du `STK001`)

## 2) Nap code

- Board: **AI Thinker ESP32-CAM**
- Chon dung cong COM.
- Upload va mo Serial Monitor (115200).

## 3) Dieu kien de test thanh cong

- Server FastAPI dang chay.
- DB ket noi duoc.
- Model AI load thanh cong (khong bi mismatch weight).
- MinIO da cau hinh env:
  - `MINIO_ENDPOINT`
  - `MINIO_ACCESS_KEY`
  - `MINIO_SECRET_KEY`
  - `MINIO_BUCKET_NAME` (neu khong set se mac dinh `smart-stick`)

## 4) Ket qua mong doi

- Serial Monitor in response HTTP tu server.
- Neu `confidence >= 30`:
  - Server gui MQTT canh bao.
  - Anh duoc upload len MinIO.
  - DB co ban ghi moi trong `detection_logs`.
- Neu `confidence < 30`:
  - Server tra `"No obstacle detected"`.
  - Khong upload MinIO, khong ghi DB.

"""
Service xử lý dữ liệu IMU: phát hiện té ngã, nhận diện trạng thái di chuyển và ước lượng vận tốc.
"""

import math
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.imu_log import IMULog
from models.stick import Stick
from core.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

# Các hằng số cấu hình thuật toán
GRAVITY_MS2 = 9.80665               # Gia tốc trọng trường chuẩn (m/s^2)
FALL_IMPACT_THRESHOLD_MS2 = 25.0    # Ngưỡng va đập mạnh (> 25 m/s^2)
FALL_TILT_THRESHOLD_DEG = 60.0      # Ngưỡng góc nghiêng nằm ngang (> 60 độ)


async def process_new_imu_data(db: AsyncSession, stick_id: str, new_log: IMULog) -> None:
    """
    Xử lý bản ghi IMU mới từ thiết bị:
    1. Truy vấn góc lệch hiệu chuẩn (Pitch/Roll offsets) từ bảng sticks.
    2. Tính toán góc Pitch/Roll và góc nghiêng (Tilt) đã hiệu chuẩn.
    3. Phát hiện té ngã dựa trên va đập mạnh kết hợp góc nghiêng đã hiệu chuẩn.
    4. Phân tích trạng thái hoạt động (Đứng yên, Đi bộ, Gậy bị đổ).
    5. Ước lượng vận tốc di chuyển tương đối (Đi chậm, Đi bình thường, Đi nhanh).
    """
    try:
        # 1. Truy vấn thông số cấu hình hiệu chuẩn của Stick
        stmt_stick = select(Stick).where(Stick.stick_id == stick_id)
        res_stick = await db.execute(stmt_stick)
        stick_obj = res_stick.scalar_one_or_none()
        
        offset_pitch = stick_obj.imu_offset_pitch if stick_obj else 0.0
        offset_roll = stick_obj.imu_offset_roll if stick_obj else 0.0

        # Lấy lịch sử 5 bản ghi gần nhất để phân tích cửa sổ thời gian (khoảng 5 giây)
        stmt_imu = (
            select(IMULog)
            .where(IMULog.stick_id == stick_id)
            .order_by(IMULog.timestamp.desc(), IMULog.id.desc())
            .limit(5)
        )
        result_imu = await db.execute(stmt_imu)
        recent_logs = list(result_imu.scalars().all())

        if not recent_logs:
            return

        # Đọc dữ liệu gia tốc thô hiện tại
        ax = new_log.acc_x or 0.0
        ay = new_log.acc_y or 0.0
        az = new_log.acc_z or 0.0

        # Tính toán gia tốc tổng hợp (m/s^2)
        curr_acc_mag = math.sqrt(ax**2 + ay**2 + az**2)
        curr_acc_ms2 = curr_acc_mag * GRAVITY_MS2

        # 2. Tính góc Pitch & Roll thô từ gia tốc
        # Pitch: xoay quanh trục X, Roll: xoay quanh trục Y
        raw_pitch = math.atan2(ay, math.sqrt(ax**2 + az**2)) * (180.0 / math.pi)
        raw_roll = math.atan2(-ax, az) * (180.0 / math.pi)

        # Áp dụng góc lệch hiệu chuẩn (Calibration offsets)
        calibrated_pitch = raw_pitch - offset_pitch
        calibrated_roll = raw_roll - offset_roll

        # Tính góc nghiêng (Tilt) hiệu chuẩn so với phương thẳng đứng
        # Cos(tilt) = Cos(pitch) * Cos(roll)
        p_rad = math.radians(calibrated_pitch)
        r_rad = math.radians(calibrated_roll)
        cos_tilt = min(1.0, max(-1.0, math.cos(p_rad) * math.cos(r_rad)))
        curr_tilt = math.degrees(math.acos(cos_tilt))

        # ── 3. THUẬT TOÁN PHÁT HIỆN TÉ NGÃ (Sử dụng góc nghiêng đã hiệu chuẩn) ──
        # Điều kiện 1: Gậy hiện tại đang nằm ngang (tilt hiệu chuẩn > 60 độ)
        is_lying_horizontal = curr_tilt > FALL_TILT_THRESHOLD_DEG

        # Điều kiện 2: Có va đập mạnh (> 25 m/s^2) trong vòng 5 giây qua
        has_recent_impact = False
        max_impact_ms2 = 0.0
        
        for log in recent_logs:
            mag = math.sqrt(
                (log.acc_x or 0) ** 2 + 
                (log.acc_y or 0) ** 2 + 
                (log.acc_z or 0) ** 2
            )
            val_ms2 = mag * GRAVITY_MS2
            if val_ms2 > max_impact_ms2:
                max_impact_ms2 = val_ms2
            if val_ms2 > FALL_IMPACT_THRESHOLD_MS2:
                has_recent_impact = True

        # Kết hợp điều kiện để xác định có té ngã hay không
        if is_lying_horizontal and has_recent_impact:
            logger.warning(
                f"[IMU/FALL] CANH BAO TE NGA! Gậy {stick_id} nằm ngang ({curr_tilt:.1f}°), "
                f"Lực va chạm gần nhất: {max_impact_ms2:.2f} m/s^2"
            )
            # Phát tín hiệu khẩn cấp đến WebSocket
            await ws_manager.broadcast_alert(stick_id, {
                "stick_id": stick_id,
                "event": "FALL_DETECTION",
                "message": "Cảnh báo khẩn cấp: Phát hiện người dùng gậy bị té ngã!",
                "timestamp": str(new_log.timestamp),
                "details": {
                    "max_impact_ms2": round(max_impact_ms2, 2),
                    "current_tilt_deg": round(curr_tilt, 1)
                }
            })

        # ── 4. PHÂN LOẠI HOẠT ĐỘNG & VẬN TỐC (Sử dụng góc nghiêng đã hiệu chuẩn) ──
        n_samples = len(recent_logs)
        acc_mags = []
        gyro_mags = []

        for log in recent_logs:
            mag_a = math.sqrt(
                (log.acc_x or 0) ** 2 + 
                (log.acc_y or 0) ** 2 + 
                (log.acc_z or 0) ** 2
            )
            mag_g = math.sqrt(
                (log.gyro_x or 0) ** 2 + 
                (log.gyro_y or 0) ** 2 + 
                (log.gyro_z or 0) ** 2
            )
            acc_mags.append(mag_a)
            gyro_mags.append(mag_g)

        # Tính độ lệch chuẩn (độ nhấp nhô/rung động)
        mean_acc = sum(acc_mags) / n_samples
        mean_gyro = sum(gyro_mags) / n_samples

        if n_samples >= 2:
            var_acc = sum((x - mean_acc) ** 2 for x in acc_mags) / (n_samples - 1)
            std_acc = math.sqrt(var_acc)
            var_gyro = sum((x - mean_gyro) ** 2 for x in gyro_mags) / (n_samples - 1)
            std_gyro = math.sqrt(var_gyro)
        else:
            std_acc = 0.0
            std_gyro = 0.0

        activity = "Không xác định"
        velocity_desc = "Đang đứng yên"

        # Phân loại hành vi
        if is_lying_horizontal and std_acc < 0.15 and std_gyro < 15.0:
            # Gậy nằm ngang thời gian dài mà không rung động mạnh
            activity = "Gậy bị đổ/Rơi"
            velocity_desc = "Đang đứng yên"
        elif std_acc < 0.08 and std_gyro < 8.0 and curr_tilt <= 35.0:
            # Dữ liệu im ắng và gậy đứng thẳng
            activity = "Đang đứng yên"
            velocity_desc = "Đang đứng yên"
        else:
            # Dữ liệu nhấp nhô, gậy ở tư thế tương đối dọc
            activity = "Đang đi bộ"
            # Tính trung bình độ lệch gia tốc động học khỏi mức trọng lực tự nhiên (1g)
            mean_dynamic_acc = sum(abs(a - 1.0) for a in acc_mags) / n_samples
            
            # Phân loại vận tốc tương đối
            if mean_dynamic_acc < 0.15 and mean_gyro < 15.0:
                velocity_desc = "Đi chậm"
            elif mean_dynamic_acc > 0.35 or mean_gyro > 45.0:
                velocity_desc = "Đi nhanh"
            else:
                velocity_desc = "Đi bình thường"

        # Broadcast trạng thái di chuyển thời gian thực qua WebSocket (Có kèm Pitch/Roll cho 3D)
        logger.info(
            f"[IMU/ACTIVITY] Gậy {stick_id} -> Hoạt động: {activity} | Vận tốc: {velocity_desc} | "
            f"Góc Pitch: {calibrated_pitch:.1f}° | Góc Roll: {calibrated_roll:.1f}° | Góc Nghiêng: {curr_tilt:.1f}°"
        )
        await ws_manager.broadcast_alert(stick_id, {
            "stick_id": stick_id,
            "event": "ACTIVITY_UPDATE",
            "timestamp": str(new_log.timestamp),
            "data": {
                "activity": activity,
                "velocity": velocity_desc,
                "tilt_deg": round(curr_tilt, 1),
                "pitch_deg": round(calibrated_pitch, 2),
                "roll_deg": round(calibrated_roll, 2),
                "pitch_calibrated": round(calibrated_pitch, 2),
                "roll_calibrated": round(calibrated_roll, 2),
                "acc_magnitude_g": round(curr_acc_mag, 3),
                "gyro_magnitude_degs": round(mean_gyro, 2)
            }
        })

    except Exception as exc:
        logger.error(f"Lỗi khi xử lý phân tích dữ liệu IMU: {exc}", exc_info=True)

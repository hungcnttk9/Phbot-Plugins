from phBot import *
import QtBind
import struct
import json
import os
import time

# Giao diện cấu hình
gui = QtBind.init(__name__, "PlayerTracking")

# Nhập tên người chơi cần theo dõi
lblPlayerName = QtBind.createLabel(gui, "Name:", 10, 10)
txtPlayerName = QtBind.createLineEdit(gui, "", 10, 30, 200, 20)

# Nhập tọa độ khu vực đào tạo
lblTrainingX = QtBind.createLabel(gui, "Point X:", 10, 60)
txtTrainingX = QtBind.createLineEdit(gui, "0", 10, 80, 100, 20)

lblTrainingY = QtBind.createLabel(gui, "Point Y:", 10, 110)
txtTrainingY = QtBind.createLineEdit(gui, "0", 10, 130, 100, 20)

lblRadius = QtBind.createLabel(gui, "Radius:", 10, 160)
txtRadius = QtBind.createLineEdit(gui, "20", 10, 180, 100, 20)

# Nút lưu cấu hình
btnSave = QtBind.createButton(gui, "save_config", "Save", 10, 220)

# Nút Bắt đầu và Kết thúc công việc
btnStart = QtBind.createButton(gui, "start_tracking", "Start", 10, 260)
btnStop = QtBind.createButton(gui, "stop_tracking", "Stop", 150, 260)

# Đường dẫn lưu cấu hình
config_path = os.path.join(get_config_path(), "PlayerTrackingConfig.json")

# Trạng thái theo dõi
is_tracking = False
is_target_nearby = False
tracking_enabled = False  # Trạng thái bật/tắt công việc theo dõi


# Hàm lưu cấu hình
def save_config():
    config = {
        "target_player_name": QtBind.text(gui, txtPlayerName),
        "training_area_x": int(QtBind.text(gui, txtTrainingX)),
        "training_area_y": int(QtBind.text(gui, txtTrainingY)),
        "radius": int(QtBind.text(gui, txtRadius)),
    }
    with open(config_path, "w") as f:
        json.dump(config, f)
    log("Đã lưu cấu hình theo dõi người chơi.")


# Hàm tải cấu hình
def load_config():
    global target_player_name, TRAINING_AREA_X, TRAINING_AREA_Y, RADIUS
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            target_player_name = config.get("target_player_name", "")
            TRAINING_AREA_X = config.get("training_area_x", 0)
            TRAINING_AREA_Y = config.get("training_area_y", 0)
            RADIUS = config.get("radius", 50)

            # Hiển thị cấu hình trên giao diện
            QtBind.setText(gui, txtPlayerName, target_player_name)
            QtBind.setText(gui, txtTrainingX, str(TRAINING_AREA_X))
            QtBind.setText(gui, txtTrainingY, str(TRAINING_AREA_Y))
            QtBind.setText(gui, txtRadius, str(RADIUS))
        log("Đã tải cấu hình theo dõi người chơi.")
    else:
        target_player_name = ""
        TRAINING_AREA_X = 0
        TRAINING_AREA_Y = 0
        RADIUS = 50


# Hàm bắt đầu công việc theo dõi
def start_tracking():
    global tracking_enabled
    tracking_enabled = True
    log("Đã bắt đầu công việc theo dõi.")


# Hàm kết thúc công việc theo dõi
def stop_tracking():
    global tracking_enabled, is_tracking
    tracking_enabled = False
    is_tracking = False
    stop_bot()  # Dừng bot nếu đang chạy
    log("Đã kết thúc công việc theo dõi.")


# Hàm kiểm tra vị trí người chơi
def handle_joymax(opcode, data):
    global is_target_nearby, is_tracking, target_player_name

    # Kiểm tra nếu công việc theo dõi đang bật
    if not tracking_enabled:
        return True

    # Opcode 0x3015: Nhận thông tin các nhân vật gần đó
    if opcode == 0x3015:
        count = struct.unpack_from("<H", data, 0)[0]
        offset = 2
        target_found = False

        for i in range(count):
            obj_data = data[offset : offset + 52]
            obj_name_length = struct.unpack_from("<B", obj_data, 36)[0]
            obj_name = data[offset + 37 : offset + 37 + obj_name_length].decode("ascii")

            # Nếu tìm thấy nhân vật cần theo dõi
            if obj_name == target_player_name:
                obj_x = struct.unpack_from("<f", obj_data, 20)[0]
                obj_y = struct.unpack_from("<f", obj_data, 24)[0]

                # Kiểm tra nếu nhân vật ở trong phạm vi
                if (
                    abs(obj_x - TRAINING_AREA_X) <= RADIUS
                    and abs(obj_y - TRAINING_AREA_Y) <= RADIUS
                ):
                    is_target_nearby = True
                    target_found = True
                    log(f"{target_player_name} đang ở trong khu vực đào tạo.")
                break
            offset += 52

        # Cập nhật trạng thái theo dõi dựa trên điều kiện
        if target_found:
            # Người chơi ở trong khu vực và trong phạm vi
            if is_bot():
                stop_bot()
                log("Ngừng botting vì người chơi đang ở gần.")
            elif not is_tracking and not is_bot():
                # Chờ 1 giây rồi bắt đầu theo dõi
                time.sleep(1)
                is_tracking = True
                log(f"Bắt đầu theo dõi {target_player_name}.")
        else:
            # Người chơi ở trong khu vực nhưng không trong phạm vi
            if is_tracking:
                is_tracking = False
                log(f"Dừng theo dõi {target_player_name}.")
            elif not is_tracking and not is_bot():
                # Bắt đầu botting vì không tìm thấy người chơi
                start_bot()
                log("Bắt đầu botting vì không tìm thấy người chơi.")

    return True


# Khởi động plugin và tải cấu hình
log("[%s] loaded" % (__name__))
load_config()

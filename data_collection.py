import os
import serial
import csv
import re
import time
import cv2
import random
import pandas as pd
import numpy as np
from datetime import datetime
from multiprocessing import Process, Event, Manager, freeze_support
import threading




def record_sensor_data(data_buffer, stop_event, recording_enabled, filename, serial_port, baud_rate):
    """ Collect EMG and IMU data when recording is enabled. """
    ser = serial.Serial(serial_port, baud_rate, timeout=1)
    print(filename)
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Time (ms)", "EMG1", "EMG2", "EMG3", "EMG4", "AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"])

        start_time = datetime.now()

        try:
            while not stop_event.is_set():
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    parts = line.split()
                    if len(parts) == 10:
                        try:
                            emg_values = list(map(int, parts[:4]))  # EMG data
                            imu_values = list(map(int, parts[4:]))  # IMU data
                            elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # ms

                            if recording_enabled.is_set():
                                # print("[INFO] Recording data...")
                                data_buffer.append([elapsed_time] + emg_values + imu_values)


                        except ValueError:
                            print(f"[WARNING] Invalid data: {line}")

            print("[INFO] Data collection finished")

        except KeyboardInterrupt:
            print("\n[INFO] Data collection manually stopped")

        finally:
            ser.close()
            print("[INFO] Serial port closed")

def run_visual_guidance(data_buffer, stop_event, recording_enabled, filename, root):
    """ Run the visual guidance, controlling when sensor data is collected """


    # ✅ 设定文件夹和文件路径
    image_folder = r"alpha"
    excel_file = r"shuffle_order.xlsx"  # 存储顺序的 Excel 文件
    csv_file = r"data_log.csv"  # 存储数据的 CSV 文件

    # ✅ 获取所有 PNG 图片
    image_files = [f for f in os.listdir(image_folder) if f.endswith(".png")]
    if not image_files:
        print("❌ 没有找到 PNG 图片，请检查文件夹！")
        exit()

    # ✅ 生成字母到数字的映射表 (A=1, B=2, ..., Z=26)
    label_dict = {chr(i + 65): i + 1 for i in range(26)}

    # ✅ **手动选择 1.png**
    image_file = "A.png"
    img_path = os.path.join(image_folder, image_file)

    if not os.path.exists(img_path):
        print(f"❌ 文件 {img_path} 不存在，请检查！")
        exit()

    # ✅ 获取图片对应的标签
    letter = image_file.split(".")[0]
    label = label_dict.get(letter, "UNKNOWN")

    # ✅ 读取或创建 Excel 文件
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file, engine='openpyxl')
    else:
        df = pd.DataFrame()

    # ✅ 记录当前的图片标签到 Excel
    new_row = pd.DataFrame([[label]])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(excel_file, index=False, engine='openpyxl')

    # ✅ 线程控制信号
    stop_event = threading.Event()
    recording_enabled = threading.Event()
    data_buffer = []  # 数据缓冲区

    # ✅ 读取并处理图片
    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None or img.size == 0:
        print(f"❌ 无法打开图片: {image_file}")
        exit()

    # ✅ 透明 PNG 处理（如果存在 Alpha 通道）
    if img.shape[-1] == 4:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]  
        white_bg = np.ones_like(bgr, dtype=np.uint8) * 255
        alpha = alpha[:, :, np.newaxis] / 255.0
        img = (bgr * alpha + white_bg * (1 - alpha)).astype(np.uint8)

    # **🔴 PREPARE STAGE (2 秒)**
    recording_enabled.clear()
    print(f"[INFO] Prepare stage for: {image_file}")

    start_time = time.time()
    for countdown in range(2, 0, -1):
        if stop_event.is_set():
            exit()
        img_copy = img.copy()
        cv2.putText(img_copy, f"Prepare: {countdown}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.imshow("Visual Guidance", img_copy)
        elapsed = time.time() - start_time
        cv2.waitKey(max(1, int((2 - elapsed) * 1000 / countdown)))  # 确保倒计时稳定
    cv2.waitKey(1)  # 立即刷新窗口

    # **🟢 GO STAGE (5 秒, 开始记录)**
    print(f"[INFO] Entering GO stage: {image_file}")
    recording_enabled.set()

    start_time = time.time()
    for countdown in range(5, 0, -1):
        if stop_event.is_set():
            exit()
        img_copy = img.copy()
        cv2.putText(img_copy, f"GO: {countdown}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("Visual Guidance", img_copy)
        elapsed = time.time() - start_time
        cv2.waitKey(max(1, int((5 - elapsed) * 1000 / countdown)))  # 确保倒计时稳定
    cv2.waitKey(1)  # 立即刷新窗口

    # **📄 结束后写入 CSV 文件**
    recording_enabled.clear()
    print(f"[INFO] GO stage complete, flushing data to CSV file...")

    if data_buffer:  # 确保有数据
        print(f"[DEBUG] Writing {len(data_buffer)} rows to file: {csv_file}")
        with open(csv_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(list(data_buffer))
        data_buffer[:] = []  # 清空缓冲区

    cv2.destroyAllWindows()
    stop_event.set()  # **停止进程**




if __name__ == '__main__':
    import serial.tools.list_ports
    print([port.device for port in serial.tools.list_ports.comports()])

    freeze_support()  # Needed for Windows multiprocessing

    manager = Manager()
    data_buffer = manager.list()
    stop_event = Event()
    recording_enabled = Event()
    
    SERIAL_PORT = 'COM4'  # Ensure this is correct
    BAUD_RATE = 115200

    data_dir = r"data\GZA"
    os.makedirs(data_dir, exist_ok=True)

    existing_files = [f for f in os.listdir(data_dir) if f.startswith("sensor_data") and f.endswith(".csv")]
    file_numbers = [int(re.search(r"sensor_data(\d+)\.csv", f).group(1)) for f in existing_files if re.search(r"sensor_data(\d+)\.csv", f)]
    next_file_number = max(file_numbers, default=0) + 1

    filename = os.path.join(data_dir, f"sensor_data{next_file_number}.csv")

    process1 = Process(
        target=record_sensor_data, 
        args=(data_buffer, stop_event, recording_enabled, filename, SERIAL_PORT, BAUD_RATE)  
    )
    process1.start()

    run_visual_guidance(data_buffer, stop_event, recording_enabled, filename, data_dir)  # **Run in the main thread**

    # **Ensure everything stops when visual guidance ends**
    stop_event.set()
    process1.terminate()
    process1.join()

    print("[INFO] All processes have safely exited")
# End of data_collection.py
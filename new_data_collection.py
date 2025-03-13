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
    print(f"[INFO] Data will be saved in: {filename}")
    
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
    """ Run the visual guidance, controlling when sensor data is collected, and repeat it 25 times. """
    image_folder = r"alpha\gestures\alpha"

    # ✅ 检查 A.png 是否存在
    image_file = "1.png"
    img_path = os.path.join(image_folder, image_file)
    if not os.path.exists(img_path):
        print(f"❌ 文件 {img_path} 不存在，请检查！")
        exit()

    img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
    if img is None or img.size == 0:
        print(f"❌ 无法打开图片: {image_file}")
        exit()

    if img.shape[-1] == 4:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]  
        white_bg = np.ones_like(bgr, dtype=np.uint8) * 255
        alpha = alpha[:, :, np.newaxis] / 255.0
        img = (bgr * alpha + white_bg * (1 - alpha)).astype(np.uint8)

        height, width = img.shape[:2]
        scale_factor = 4
        new_size = (width * scale_factor, height * scale_factor)
        img = cv2.resize(img, new_size, interpolation=cv2.INTER_CUBIC) 

    for trial in range(1, 26):
        if stop_event.is_set():
            break  # 终止所有循环

        recording_enabled.clear()
        print(f"[INFO] Trial {trial}: Prepare stage for {image_file}")

        start_time = time.time()
        for countdown in range(2, 0, -1):
            if stop_event.is_set():
                return
            img_copy = img.copy()
            cv2.putText(img_copy, f"Trial {trial}: Prepare {countdown}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Visual Guidance", img_copy)
            elapsed = time.time() - start_time
            cv2.waitKey(max(1, int((2 - elapsed) * 1000 / countdown)))  
        cv2.waitKey(1)

        # **🟢 GO STAGE (5 秒, 开始记录)**
        print(f"[INFO] Trial {trial}: GO stage started for {image_file}")
        recording_enabled.set()

        start_time = time.time()
        for countdown in range(5, 0, -1):
            if stop_event.is_set():
                return
            img_copy = img.copy()
            cv2.putText(img_copy, f"Trial {trial}: GO {countdown}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Visual Guidance", img_copy)
            elapsed = time.time() - start_time
            cv2.waitKey(max(1, int((5 - elapsed) * 1000 / countdown)))  
        cv2.waitKey(1)

        # **📄 结束后写入 CSV 文件**
        recording_enabled.clear()
        print(f"[INFO] Trial {trial}: GO stage complete, saving data...")

        # if data_buffer:  # 确保有数据
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(list(data_buffer))
            writer.writerow([])
        data_buffer[:] = []  # 清空缓冲区

        time.sleep(2)  # 额外的休息时间，确保节奏稳定

    print("[INFO] All 25 trials completed!")
    cv2.destroyAllWindows()
    stop_event.set()  # **停止进程**


if __name__ == '__main__':
    import serial.tools.list_ports
    print([port.device for port in serial.tools.list_ports.comports()])

    freeze_support()  # Windows 多进程支持

    manager = Manager()
    data_buffer = manager.list()
    stop_event = Event()
    recording_enabled = Event()
    
    SERIAL_PORT = 'COM4'  # 确保端口正确
    BAUD_RATE = 115200

    data_dir = r"new_collect\fzh"
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

    run_visual_guidance(data_buffer, stop_event, recording_enabled, filename, data_dir)

    stop_event.set()
    process1.terminate()
    process1.join()

    print("[INFO] All processes have safely exited")

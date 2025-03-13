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
    """ 采集 EMG 和 IMU 数据，仅在 recording_enabled 允许时记录 """
    ser = serial.Serial(serial_port, baud_rate, timeout=1)

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
                            emg_values = list(map(int, parts[:4]))  # EMG 数据
                            imu_values = list(map(int, parts[4:]))  # IMU 数据
                            elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # 毫秒计算

                            if recording_enabled.is_set():
                                data_buffer.append([elapsed_time] + emg_values + imu_values)

                        except ValueError:
                            print(f"[WARNING] 无效数据: {line}")

            print("[INFO] 数据采集完成")

        except KeyboardInterrupt:
            print("\n[INFO] 手动停止数据采集")

        finally:
            ser.close()
            print("[INFO] 串口已关闭")

def run_visual_guidance(data_buffer, stop_event, recording_enabled, filename, root):
    """ 控制视觉引导，按 A-E 顺序进行数据采集 """

    image_folder = r"alpha"
    image_files = sorted([f for f in os.listdir(image_folder) if f.endswith(".png")])  # **确保按顺序**
    label_dict = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}  # **固定 A-E 顺序**
    excel_file = os.path.join(root, "shuffle_order.xlsx")

    # **按固定顺序匹配图片**
    image_map = {file: label_dict[file.split(".")[0]] for file in image_files if file.split(".")[0] in label_dict}
    ordered_images = [file for file in image_files if file.split(".")[0] in label_dict]  # **按 A-E 顺序**
    ordered_labels = [image_map[file] for file in ordered_images]

    # **存储顺序到 Excel**
    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file, engine='openpyxl')
    else:
        df = pd.DataFrame()

    new_row = pd.DataFrame([ordered_labels])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(excel_file, index=False, engine='openpyxl')

    # **按顺序引导**
    for i, image_file in enumerate(ordered_images):
        if stop_event.is_set():
            break

        img_path = os.path.join(image_folder, image_file)
        print(f"[INFO] 加载图片: {img_path}")

        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is None or img.size == 0:
            print(f"[WARNING] 无法加载图片: {image_file}")
            continue

        # **准备阶段**
        recording_enabled.clear()
        for countdown in range(5, 0, -1):
            if stop_event.is_set():
                return
            img_copy = img.copy()
            cv2.putText(img_copy, f"Prepare: {countdown}, No.{i+1}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Visual Guidance", img_copy)
            cv2.waitKey(1000)

        # **GO 阶段**
        print(f"[INFO] 进入 GO 阶段: {image_file}")
        recording_enabled.set()

        for countdown in range(5, 0, -1):
            if stop_event.is_set():
                return
            img_copy = img.copy()
            cv2.putText(img_copy, f"GO: {countdown}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Visual Guidance", img_copy)
            cv2.waitKey(1000)

        recording_enabled.clear()
        print(f"[INFO] 采集完成，写入数据文件")

        # **写入数据**
        if data_buffer:
            print(f"[DEBUG] 写入 {len(data_buffer)} 行数据到: {filename}")
            with open(filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(list(data_buffer))
            data_buffer[:] = []

        cv2.destroyAllWindows()

    stop_event.set()

if __name__ == '__main__':
    import serial.tools.list_ports
    print([port.device for port in serial.tools.list_ports.comports()])

    freeze_support()

    manager = Manager()
    data_buffer = manager.list()
    stop_event = Event()
    recording_enabled = Event()
    
    SERIAL_PORT = 'COM4'
    BAUD_RATE = 115200

    data_dir = r"data\GZA_5"
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

    print("[INFO] 所有进程安全退出")

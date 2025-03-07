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
from multiprocessing import Process, Event
import threading
import keyboard  # 监听键盘输入

# 采集数据的全局控制变量
stop_event = Event()

# 配置串口
SERIAL_PORT = 'COM4'  # 你的串口号
BAUD_RATE = 115200


def record_sensor_data():
    """ 采集 EMG 和 IMU 数据，直到 `stop_event` 触发 """
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except serial.SerialException:
        print("[ERROR] 无法打开串口，请检查设备连接！")
        return

    # 确保文件夹存在
    data_dir = r"data\FZH"
    os.makedirs(data_dir, exist_ok=True)

    # 找到最新的文件编号
    existing_files = [f for f in os.listdir(data_dir) if f.startswith("sensor_data") and f.endswith(".csv")]
    file_numbers = [int(re.search(r"sensor_data(\d+)\.csv", f).group(1)) for f in existing_files if re.search(r"sensor_data(\d+)\.csv", f)]

    # 计算下一个文件编号
    next_file_number = max(file_numbers, default=0) + 1

    # 生成新的 CSV 文件名
    filename = os.path.join(data_dir, f"sensor_data{next_file_number}.csv")
    print(f"[INFO] 采集数据存储到: {filename}")

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Time (ms)", "EMG1", "EMG2", "EMG3", "EMG4", "AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"])

        start_time = datetime.now()
        data_count = 0  # 计数器，确保数据被写入

        try:
            while not stop_event.is_set():
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    parts = line.split()  # 以空格分割数据
                    if len(parts) == 10:  # 确保数据格式正确
                        try:
                            emg_values = list(map(int, parts[:4]))  # 解析 EMG 数据
                            imu_values = list(map(int, parts[4:]))  # 解析 IMU 数据
                            
                            elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # 计算时间（毫秒）

                            # **写入 CSV 文件**
                            writer.writerow([elapsed_time] + emg_values + imu_values)
                            data_count += 1

                            # **每 10 行输出一次日志**
                            if data_count % 10 == 0:
                                print(f"[INFO] 数据写入 {data_count} 行")

                        except ValueError:
                            print(f"[WARNING] 无效数据: {line}")  # 处理非整数值
                else:
                    print("[WARNING] 串口未接收到数据，请检查设备！")

            print(f"[INFO] 采集结束，已存储 {data_count} 行数据")

        except KeyboardInterrupt:
            print("\n[INFO] 采集进程手动停止")
        
        finally:
            ser.close()
            print("[INFO] 串口已关闭")


def run_visual_guidance():
    """ 运行视觉指导程序并在结束后停止数据采集 """
    image_folder = r"alpha"
    path = r"data\FZH"
    os.makedirs(path, exist_ok=True)
    excel_file = r"data\FZH\shuffle_order.xlsx"

    # 获取所有 PNG 图片
    image_files = [f for f in os.listdir(image_folder) if f.endswith(".png")]

    # 生成标签映射 (A->1, B->2, ..., Z->26)
    label_dict = {chr(i + 65): i + 1 for i in range(1)}  # 'A' -> 1, ..., 'Z' -> 26

    # 过滤并映射文件名
    image_map = {file: label_dict[file.split(".")[0]] for file in image_files if file.split(".")[0] in label_dict}

    # 打乱顺序
    shuffled_images = list(image_map.keys())
    random.shuffle(shuffled_images)

    # **OpenCV 显示主循环**
    for i, image_file in enumerate(shuffled_images):
        if stop_event.is_set():
            break

        img_path = os.path.join(image_folder, image_file)
        print(f"[INFO] 加载图片: {img_path}")

        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is not None and img.size > 0:
            letter = image_file.split(".")[0]
            print(f"[INFO] 进入准备阶段: {letter}, 标签: {image_map[image_file]}")

            # **倒计时**
            for countdown in range(5, 0, -1):
                if stop_event.is_set():
                    break
                img_copy = img.copy()
                cv2.putText(img_copy, f"Prepare: {countdown}", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                cv2.imshow("Visual Guidance", img_copy)
                cv2.waitKey(1000)

        else:
            print(f"[WARNING] 无法打开图片: {image_file}")

    print("\n[INFO] 视觉指导结束，停止数据采集")
    stop_event.set()
    cv2.destroyAllWindows()


def monitor_keyboard():
    """ 监听键盘，如果按下 'q' 键，则停止所有进程 """
    while True:
        if keyboard.is_pressed('q'):
            print("\n[INFO] 你按下了 'q'，正在停止所有进程...")
            stop_event.set()
            break
        time.sleep(0.1)


if __name__ == "__main__":
    # 启动数据采集进程
    process1 = Process(target=record_sensor_data)
    process1.start()

    # 启动视觉指导（用 `threading` 以防止 `cv2.imshow()` 出问题）
    visual_thread = threading.Thread(target=run_visual_guidance)
    visual_thread.start()

    # 启动键盘监听线程
    keyboard_thread = threading.Thread(target=monitor_keyboard)
    keyboard_thread.start()

    # **等待视觉指导结束**
    visual_thread.join()
    stop_event.set()
    process1.join()  # **等待数据写入**
    keyboard_thread.join()

    print("[INFO] 所有进程已安全退出")

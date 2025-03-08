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
    """ Run the visual guidance, controlling when sensor data is collected """

    image_folder = r"alpha"
    image_files = [f for f in os.listdir(image_folder) if f.endswith(".png")]
    label_dict = {chr(i + 65): i + 1 for i in range(5)}  # 仅限 A-E
    excel_file = os.path.join(root, "shuffle_order.xlsx")
    
    image_map = {file: label_dict[file.split(".")[0]] for file in image_files if file.split(".")[0] in label_dict}

    shuffled_images = random.sample([f for f in image_files if f.split(".")[0] in label_dict], 5)  # 仅随机 A-E
    shuffled_labels = [image_map[file] for file in shuffled_images]

    if os.path.exists(excel_file):
        df = pd.read_excel(excel_file, engine='openpyxl')
    else:
        df = pd.DataFrame()

    new_row = pd.DataFrame([shuffled_labels])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel(excel_file, index=False, engine='openpyxl')

    i = 0
    for image_file in shuffled_images:
        if stop_event.is_set():
            break

        img_path = os.path.join(image_folder, image_file)
        print(f"[INFO] Loading image: {img_path}")

        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is None or img.size == 0:
            print(f"[WARNING] Unable to load image: {image_file}")
            continue

        recording_enabled.clear()
        for countdown in range(5, 0, -1):
            if stop_event.is_set():
                return
            img_copy = img.copy()
            cv2.putText(img_copy, f"Prepare: {countdown}, No.{i}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Visual Guidance", img_copy)
            cv2.waitKey(1000)
        i += 1

        print(f"[INFO] Entering GO stage: {image_file}")
        recording_enabled.set()

        for countdown in range(5, 0, -1):
            if stop_event.is_set():
                return
            img_copy = img.copy()
            cv2.putText(img_copy, f"GO: {countdown}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Visual Guidance", img_copy)
            cv2.waitKey(1000)

        recording_enabled.clear()
        print(f"[INFO] GO stage complete, flushing data to file")

        if data_buffer:
            print(f"[DEBUG] Writing {len(data_buffer)} rows to file: {filename}")
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

    print("[INFO] All processes have safely exited")

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

def run_visual_guidance(data_buffer, stop_event, recording_enabled, filename):
    """ Run the visual guidance, controlling when sensor data is collected """

    image_folder = r"alpha"
    image_files = [f for f in os.listdir(image_folder) if f.endswith(".png")]
    shuffled_images = random.sample(image_files, 2)  # Shuffle images len(image_files)

    for image_file in shuffled_images:
        if stop_event.is_set():
            break

        img_path = os.path.join(image_folder, image_file)
        print(f"[INFO] Loading image: {img_path}")

        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if img is None or img.size == 0:
            print(f"[WARNING] Unable to load image: {image_file}")
            continue

        # **PREPARE STAGE (No recording)**
        recording_enabled.clear()
        for countdown in range(5, 0, -1):
            if stop_event.is_set():
                return
            img_copy = img.copy()
            cv2.putText(img_copy, f"Prepare: {countdown}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow("Visual Guidance", img_copy)
            cv2.waitKey(1000)

        # **GO STAGE (Start recording)**
        print(f"[INFO] Entering GO stage: {image_file}")
        recording_enabled.set()

        for countdown in range(5, 0, -1):
            if stop_event.is_set():
                return
            img_copy = img.copy()
            cv2.putText(img_copy, f"GO: {countdown}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow("Visual Guidance", img_copy)
            cv2.waitKey(1000)

        # **END OF GO (Write buffered data)**
        recording_enabled.clear()
        print(f"[INFO] GO stage complete, flushing data to file")

        if data_buffer:  # Ensure there's data before writing
            print(f"[DEBUG] Writing {len(data_buffer)} rows to file: {filename}")  # Debugging print
            with open(filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(list(data_buffer))
            data_buffer[:] = []  # Clear buffer after writing

        cv2.destroyAllWindows()

    stop_event.set()  # **Automatically stop all processes when visual guidance ends**

if __name__ == '__main__':
    import serial.tools.list_ports
    print([port.device for port in serial.tools.list_ports.comports()])

    freeze_support()  # Needed for Windows multiprocessing

    manager = Manager()
    data_buffer = manager.list()
    stop_event = Event()
    recording_enabled = Event()
    
    SERIAL_PORT = 'COM3'  # Ensure this is correct
    BAUD_RATE = 115200

    data_dir = r"data\FZH"
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

    run_visual_guidance(data_buffer, stop_event, recording_enabled, filename)  # **Run in the main thread**

    # **Ensure everything stops when visual guidance ends**
    stop_event.set()
    process1.terminate()
    process1.join()

    print("[INFO] All processes have safely exited")

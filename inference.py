import threading
import serial
import csv
import os
import time
import numpy as np
from datetime import datetime
from collections import deque
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler

# **全局变量**
data_buffer = deque(maxlen=5000)  # 5s 数据缓存
stop_event = threading.Event()

# **串口配置**
SERIAL_PORT = "COM4"  # 修改为 Arduino 端口
BAUD_RATE = 115200
FILENAME = "sensor_data.csv"

# **LSTM 模型**
MODEL_PATH = "new_collect/fzh/rnn_emg_model.h5"

# **传感器数据格式 (EMG + IMU)**
NUM_CHANNELS = 10  # 4 EMG + 6 IMU
WINDOW_SIZE = 1000  # 5s 数据 (1000ms * 5)
STRIDE = 50  # 每 50ms 处理一次
TIME_STEPS = 100  # LSTM 期望的 time_steps
NUM_WINDOWS = 19  # 计算得到的时间窗口数量

# **归一化**
scaler = StandardScaler()

# **加载 LSTM 模型**
if os.path.exists(MODEL_PATH):
    model = load_model(MODEL_PATH)
    print("✅ LSTM Model loaded successfully!")
else:
    raise FileNotFoundError(f"❌ Model file not found at {MODEL_PATH}")

# **数据采集线程**
def record_sensor_data():
    """ 从 Arduino 读取传感器数据 (EMG + IMU) 并存入 data_buffer """
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except serial.SerialException as e:
        print(f"❌ 串口错误: {e}")
        return

    print(f"[INFO] ✅ 开始采集数据，存入: {FILENAME}")

    with open(FILENAME, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Time (ms)", "EMG1", "EMG2", "EMG3", "EMG4", "AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"])

        start_time = datetime.now()
        try:
            while not stop_event.is_set():
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    parts = line.split()
                    if len(parts) == 10:  # 确保数据完整
                        try:
                            emg_values = list(map(int, parts[:4]))  # EMG 数据
                            imu_values = list(map(int, parts[4:]))  # IMU 数据
                            elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # 毫秒

                            # 存入队列
                            data_buffer.append([elapsed_time] + emg_values + imu_values)

                        except ValueError:
                            print(f"[WARNING] ❗ 数据解析失败: {line}")

            print("[INFO] ✅ 数据采集完成")
        except KeyboardInterrupt:
            print("\n[INFO] 🛑 手动停止数据采集")
        finally:
            ser.close()
            print("[INFO] ✅ 串口已关闭")

# **数据预处理线程**
def data_preprocess():
    """ 每 0.5s 读取 5s 数据，并进行窗口化处理 """
    while not stop_event.is_set():
        if len(data_buffer) < WINDOW_SIZE:
            time.sleep(0.1)  # 缓冲数据不足时等待
            continue

        # 获取最新 5s 数据
        recent_data = list(data_buffer)[-WINDOW_SIZE:]

        # 转换为 NumPy 数组 (1000, 10)
        data_array = np.array(recent_data)[:, 1:]  # 移除时间戳，只保留 EMG & IMU

        # **归一化**
        data_array = scaler.fit_transform(data_array)

        # **构建滑动窗口**
        windows = []
        for start in range(0, WINDOW_SIZE - TIME_STEPS + 1, STRIDE):  # 1000-100+1，确保19个窗口
            windows.append(data_array[start:start + TIME_STEPS])  # (100, 10)

        # **转换形状 (19, 100, 10)**
        windows = np.array(windows)

        # **调整形状为 (1, 19, 1000)**
        processed_windows = windows.reshape(1, NUM_WINDOWS, TIME_STEPS * NUM_CHANNELS)

        # 存入全局变量
        global processed_data
        processed_data = processed_windows

        # print(f"[INFO] ✅ 预处理完成: {processed_windows.shape}")

        time.sleep(0.5)  # 0.5s 运行一次


# **预测线程**
def prediction():
    """ 每 0.5s 运行一次预测 """
    while not stop_event.is_set():
        if 'processed_data' not in globals():
            time.sleep(0.1)
            continue

        # 获取最近的预处理数据
        input_data = processed_data  # (1, 19, 1000)

        # **进行预测**
        predictions = model.predict(input_data,verbose=0)
        predicted_label = np.argmax(predictions, axis=1)

        print(f"🔮 预测结果: {predicted_label}")

        time.sleep(0.1)  # 每 0.5s 预测一次

# **启动多线程**
def start_threads():
    """ 启动数据采集、预处理和预测线程 """
    # 线程 1：数据采集
    thread_record = threading.Thread(target=record_sensor_data, daemon=True)

    # 线程 2：数据预处理
    thread_preprocess = threading.Thread(target=data_preprocess, daemon=True)

    # 线程 3：实时预测
    thread_predict = threading.Thread(target=prediction, daemon=True)

    # 启动线程
    thread_record.start()
    thread_preprocess.start()
    thread_predict.start()

    return thread_record, thread_preprocess, thread_predict

# **运行主程序**
if __name__ == "__main__":
    print("[INFO] 🚀 启动 EMG 识别系统")

    # 启动线程
    threads = start_threads()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] 🛑 终止所有线程...")
        stop_event.set()
        for t in threads:
            t.join()

    print("[INFO] ✅ 系统已安全关闭")

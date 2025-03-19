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
SERIAL_PORT = "COM3"  # 修改为 Arduino 端口
BAUD_RATE = 115200
FILENAME = "sensor_data.csv"

# **LSTM 模型**


# **传感器数据格式 (EMG + IMU)**
NUM_CHANNELS = 10  # 4 EMG + 6 IMU
WINDOW_SIZE = 1000  # 5s 数据 (1000ms * 5)
STRIDE = 50  # 每 50ms 处理一次
TIME_STEPS = 100  # LSTM 期望的 time_steps
NUM_WINDOWS = 19  # 计算得到的时间窗口数量

FEATURE = True
EMG = True

CHOSSEN_CHANNELS = 4 if EMG else 10
MODEL_PATH = "weights/cnn_emg_model_emg.h5" if EMG else "weights/cnn_emg_model_all_channels.h5"
# **归一化**
scaler = StandardScaler()

# **加载 LSTM 模型**
if os.path.exists(MODEL_PATH):
    model = load_model(MODEL_PATH)
    print(" LSTM Model loaded successfully!")
else:
    raise FileNotFoundError(f" Model file not found at {MODEL_PATH}")

def detect_action(X):
    if np.max(X[:,0:6,:,8])>5000 or np.max(X[:,0:6,:,9])>5000:
        return True
    else:
        return False

def extract_emg_features(signal, fs=1000):
    """Extracts features from an EMG signal (100 time steps)."""
    mav = np.mean(np.abs(signal))  # Mean Absolute Value
    rms = np.sqrt(np.mean(signal**2))  # Root Mean Square
    var = np.var(signal)  # Variance
    zc = np.sum(np.diff(np.sign(signal)) != 0)  # Zero Crossing Count
    wl = np.sum(np.abs(np.diff(signal)))  # Waveform Length

    # Frequency-domain features using FFT
    fft_vals = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(len(signal), d=1/fs)
    power = np.abs(fft_vals)**2
    total_power = np.sum(power)
    mean_freq = np.sum(freqs * power) / total_power if total_power else 0

    cumsum_power = np.cumsum(power)
    median_freq = freqs[np.where(cumsum_power >= total_power/2)[0][0]] if total_power else 0

    return np.array([mav, rms, var, zc, wl, mean_freq, median_freq])

def synthesize_time_series(features, num_timesteps=100):
    """
    Generates a synthetic time series of length `num_timesteps` from extracted features.
    Uses Gaussian noise centered at the mean feature values.
    """
    synthesized_signal = np.zeros((num_timesteps,))
    
    for i, feature in enumerate(features):
        synthesized_signal += feature * np.sin(2 * np.pi * (i + 1) * np.linspace(0, 1, num_timesteps))
    
    return synthesized_signal + np.random.normal(0, 0.05, num_timesteps)  # Add small noise

def replace_emg_with_synthetic_data(X, fs=1000):
    """
    Replaces the first 4 EMG channels in each window with synthesized time series
    generated from extracted features, while keeping the last 6 IMU channels unchanged.

    Parameters:
    - X: Shape (num_samples, num_windows, num_timesteps, num_channels)
    - fs: Sampling frequency

    Returns:
    - X_new: Same shape as X, but with EMG channels replaced by synthetic features
    """
    num_samples, num_windows, num_timesteps, num_channels = X.shape
    new_X = np.copy(X) 
    for i in range(num_samples):
        for j in range(num_windows):
            for ch in range(CHOSSEN_CHANNELS):  # Replace only the first 4 EMG channels
                features = extract_emg_features(X[i, j, :, ch], fs)
                new_X[i, j, :, ch] = synthesize_time_series(features, num_timesteps)

    return new_X

# **数据采集线程**
def record_sensor_data():
    """ 从 Arduino 读取传感器数据 (EMG + IMU) 并存入 data_buffer """
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except serial.SerialException as e:
        print(f"串口错误: {e}")
        return

    print(f"[INFO] 开始采集数据，存入: {FILENAME}")

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
                            print(f"[WARNING]  数据解析失败: {line}")

            print("[INFO] 数据采集完成")
        except KeyboardInterrupt:
            print("\n[INFO] 手动停止数据采集")
        finally:
            ser.close()
            print("[INFO] 串口已关闭")

# **数据预处理线程**
def data_preprocess():
    """ 每 0.1s 读取 5s 数据，并进行窗口化处理 """
    while not stop_event.is_set():
        if len(data_buffer) < WINDOW_SIZE:
            time.sleep(0.1)  # 缓冲数据不足时等待
            continue

        recent_data = list(data_buffer)[-WINDOW_SIZE:]
        data_array = np.array(recent_data)[:, 1:]  # 移除时间戳，只保留 EMG & IMU
        # data_array = scaler.fit_transform(data_array)
        windows = []
        for start in range(0, WINDOW_SIZE - TIME_STEPS + 1, STRIDE):  # 1000-100+1，确保19个窗口
            windows.append(data_array[start:start + TIME_STEPS])  # (100, 10)
        
        windows = np.array(windows)
        
        processed_windows = windows.reshape(1, NUM_WINDOWS, TIME_STEPS * NUM_CHANNELS)
        processed_windows_original = processed_windows.reshape(1, NUM_WINDOWS, TIME_STEPS,  NUM_CHANNELS)
        if FEATURE:
            processed_windows = replace_emg_with_synthetic_data(processed_windows_original, fs=1000)
            flag = detect_action(processed_windows_original)
            global FLAG 
            FLAG = flag
            
        global processed_data
        processed_data = processed_windows.reshape(1, NUM_WINDOWS, TIME_STEPS * NUM_CHANNELS)

        time.sleep(0.2)  # 0.2s 运行一次


# **预测线程**
def prediction():
    """ 每 0.5s 运行一次预测 """
    while not stop_event.is_set():
        if 'processed_data' not in globals() or 'FLAG' not in globals():
            time.sleep(0.1)
            continue
        if not FLAG:
            print(f"No action")
            continue

        input_data = processed_data  # (1, 19, 1000)

        # **进行预测**
        predictions = model.predict(input_data,verbose=0)
        predicted_label = np.argmax(predictions, axis=1)
        print(f"prediction result: {predicted_label}")

        # time.sleep(0.1)  

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
    print("[INFO] 启动 EMG 识别系统")

    # 启动线程
    threads = start_threads()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] 终止所有线程...")
        stop_event.set()
        for t in threads:
            t.join()

    print("[INFO] 系统已安全关闭")

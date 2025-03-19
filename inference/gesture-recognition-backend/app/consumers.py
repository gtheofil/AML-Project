import json
import numpy as np
import asyncio
from collections import deque
from channels.generic.websocket import AsyncWebsocketConsumer
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler
# from .your_feature_functions import extract_emg_features, synthesize_time_series, replace_emg_with_synthetic_data  # 导入特征提取和数据处理函数

# **全局变量**
data_buffer = deque(maxlen=5000)  # 5秒数据缓存
TIME_STEPS = 100  # LSTM 输入时间步长
STRIDE = 50  # 计算滑动窗口步长，每50ms一次
NUM_CHANNELS = 10  # 4 EMG + 6 IMU
NUM_WINDOWS = (1000 - TIME_STEPS) // STRIDE + 1  # 计算窗口数量
scaler = StandardScaler()

# **LSTM 模型路径更新**
MODEL_PATH = r"E:\MSC\AML\AML-Project\weights\cnn_emg_model_emg.h5"  # 更新为正确的模型路径
model = load_model(MODEL_PATH)
def detect_action(X):
    # print(X.shape)
    if np.max(X[:,0:6,:,8])>5000 or np.max(X[:,0:6,:,9])>5000:
        return True
    else:
        return False
# **特征提取函数**
def extract_emg_features(signal, fs=1000):
    """从EMG信号中提取特征（100个时间步）"""
    mav = np.mean(np.abs(signal))  # 平均绝对值
    rms = np.sqrt(np.mean(signal**2))  # 均方根
    var = np.var(signal)  # 方差
    zc = np.sum(np.diff(np.sign(signal)) != 0)  # 零交叉计数
    wl = np.sum(np.abs(np.diff(signal)))  # 波形长度

    # 频率域特征，使用FFT
    fft_vals = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(len(signal), d=1/fs)
    power = np.abs(fft_vals)**2
    total_power = np.sum(power)
    mean_freq = np.sum(freqs * power) / total_power if total_power else 0

    cumsum_power = np.cumsum(power)
    median_freq = freqs[np.where(cumsum_power >= total_power/2)[0][0]] if total_power else 0

    return np.array([mav, rms, var, zc, wl, mean_freq, median_freq])

# **合成时间序列函数**
def synthesize_time_series(features, num_timesteps=100):
    """从提取的特征生成一个合成的时间序列"""
    synthesized_signal = np.zeros((num_timesteps,))
    
    for i, feature in enumerate(features):
        synthesized_signal += feature * np.sin(2 * np.pi * (i + 1) * np.linspace(0, 1, num_timesteps))
    
    return synthesized_signal + np.random.normal(0, 0.05, num_timesteps)  # 添加小噪声

# **替换 EMG 为合成数据函数**
def replace_emg_with_synthetic_data(X, fs=1000):
    """
    用提取的特征生成合成时间序列，替换 EMG 数据
    """
    num_samples, num_windows, num_timesteps, num_channels = X.shape
    new_X = np.copy(X)  # 创建新数组

    for i in range(num_samples):
        for j in range(num_windows):
            for ch in range(4):  # 替换前 4 个 EMG 通道
                features = extract_emg_features(X[i, j, :, ch], fs)
                new_X[i, j, :, ch] = synthesize_time_series(features, num_timesteps)

    return new_X

class GestureRecognitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("[INFO] WebSocket 连接已建立")
        self.running = True
        asyncio.create_task(self.send_periodic_predictions())

    async def receive(self, text_data=None):
        """接收 Arduino 传感器数据, 存入 buffer"""
        if text_data is None:
            return
        try:
            data = json.loads(text_data)
            emg_values = list(map(int, data.get("emg", [])))  # 4 通道 EMG
            imu_values = list(map(int, data.get("acc", []) + data.get("gyro", [])))  # 6 轴 IMU

            if len(emg_values) == 4 and len(imu_values) == 6:
                data_buffer.append(emg_values + imu_values)
            else:
                print(f"[WARNING] 数据长度异常: EMG={len(emg_values)}, IMU={len(imu_values)}")
        except json.JSONDecodeError:
            print("[ERROR] JSON 数据解析失败")
        except Exception as e:
            print(f"[ERROR] 数据处理错误: {e}")

    async def send_periodic_predictions(self):
        """每 0.5 秒进行一次预测并发送数据"""
        while self.running:
            if len(data_buffer) >= 5000:
                await self.run_prediction()
            await asyncio.sleep(0.1)

    async def run_prediction(self):
        """读取最近 5s 数据，滑动窗口化，并进行预测"""
        if len(data_buffer) < 5000:
            print("[WARNING] 数据不足 5s, 无法进行预测")
            return

        # 获取最近 5s 数据
        recent_data = np.array(list(data_buffer)[-1000:])  # (5000, 10)
        recent_data_o = np.array(list(data_buffer)[-5000:])  # (5000, 10)
        # scaled_data = scaler.fit_transform(recent_data)  # 归一化

        # 滑动窗口处理
        windows = []
        for start in range(0, 5000 - TIME_STEPS + 1, STRIDE):
            if start + TIME_STEPS <= len(recent_data):  # 确保不会越界
                windows.append(recent_data[start:start + TIME_STEPS].flatten())

        # 转换成 NumPy 数组
        windows_array = np.array(windows)
        
        # print(f"[DEBUG] 滑动窗口 shape: {windows_array.shape}")

        # 确保形状匹配
        expected_shape = (NUM_WINDOWS, TIME_STEPS * NUM_CHANNELS)
        if windows_array.shape != expected_shape:
            print(f"[ERROR] 数据尺寸不匹配, 当前: {windows_array.shape}, 期望: {expected_shape}")
            return

        # 进行 reshape
        try:
            processed_windows = windows_array.reshape(1, NUM_WINDOWS, TIME_STEPS * NUM_CHANNELS)
            processed_windows_original = processed_windows.reshape(1, NUM_WINDOWS, TIME_STEPS, NUM_CHANNELS)
            flag = detect_action(processed_windows_original)
        except ValueError as e:
            print(f"[ERROR] 维度错误: {e}, windows.shape={windows_array.shape}")
            return

        # 替换 EMG 数据为合成数据
        processed_windows = replace_emg_with_synthetic_data(processed_windows_original, fs=1000)

        processed_windows = processed_windows.reshape(1, NUM_WINDOWS, TIME_STEPS * NUM_CHANNELS)
        # 运行预测
        predictions = model.predict(processed_windows, verbose=0)
        predicted_class = int(np.argmax(predictions, axis=1))

        print(f"[DEBUG] 预测结果: {predicted_class+1}")
        flag = True
        if flag:# 发送分类结果 & 波形
            try:
                await self.send(json.dumps({
                    "gesture": predicted_class+1,
                    "waveform": np.ones_like(recent_data_o[-5000:].transpose()).tolist(),  # 发送最近 5000ms 波形
                    "highlight_range": [4000, 5000]  # 高亮最近 1s 数据
                }))
            except Exception as e:
                print(f"[ERROR] WebSocket 发送失败: {e}")

    async def disconnect(self, close_code):
        print("[INFO] WebSocket 断开")
        self.running = False

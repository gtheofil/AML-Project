import json
import numpy as np
from collections import deque
from channels.generic.websocket import AsyncWebsocketConsumer
from tensorflow.keras.models import load_model

# 加载 LSTM 预测模型
MODEL_PATH = r"E:\MSC\AML\AML-Project\new_collect\fzh\cnn_emg_model.h5"
model = load_model(MODEL_PATH)

# **全局变量**
data_buffer = deque(maxlen=5000)  # 5秒数据缓存
TIME_STEPS = 100  # LSTM 输入时间步长
STRIDE = 272  # 计算合适的滑动窗口步长
NUM_CHANNELS = 10  # 4 EMG + 6 IMU
NUM_WINDOWS = (5000 - TIME_STEPS) // STRIDE + 1  # 自动计算窗口数量

class GestureRecognitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("[INFO] WebSocket 连接已建立")

    async def receive(self, text_data):
        """ 接收 Arduino 传感器数据, 存入 buffer """
        try:
            data = json.loads(text_data)
            emg_values = list(map(int, data.get("emg", [])))  # 4 通道 EMG
            imu_values = list(map(int, data.get("acc", []) + data.get("gyro", [])))  # 6 轴 IMU

            if len(emg_values) == 4 and len(imu_values) == 6:
                data_buffer.append(emg_values + imu_values)
            else:
                print(f"[WARNING] 数据长度异常: EMG={len(emg_values)}, IMU={len(imu_values)}")

            # 仅每 500ms 运行一次预测
            if len(data_buffer) >= 5000 and len(data_buffer) % 500 == 0:
                await self.run_prediction()
        except json.JSONDecodeError:
            print("[ERROR] JSON 数据解析失败")
        except Exception as e:
            print(f"[ERROR] 数据处理错误: {e}")

    async def run_prediction(self):
        """ 读取最近 5s 数据，滑动窗口化，并进行预测 """
        if len(data_buffer) < 5000:
            print("[WARNING] 数据不足 5s, 无法进行预测")
            return

        # 获取最近 5s 数据
        recent_data = np.array(list(data_buffer)[-5000:])  # (5000, 10)

        # 滑动窗口处理
        windows = []
        for start in range(0, 5000 - TIME_STEPS + 1, STRIDE):
            windows.append(recent_data[start:start + TIME_STEPS].flatten())  # (1000,)

        # 转换成 NumPy 数组
        windows_array = np.array(windows)

        # 确保形状匹配
        expected_shape = (NUM_WINDOWS, TIME_STEPS * NUM_CHANNELS)
        if windows_array.shape != expected_shape:
            print(f"[ERROR] 数据尺寸不匹配, 当前: {windows_array.shape}, 期望: {expected_shape}")
            return

        # 进行 reshape
        processed_windows = windows_array.reshape(1, NUM_WINDOWS, TIME_STEPS * NUM_CHANNELS)

        # 运行预测
        predictions = model.predict(processed_windows, verbose=0)
        predicted_class = int(np.argmax(predictions, axis=1))

        # 发送分类结果 & 波形
        await self.send(json.dumps({
            "gesture": predicted_class,
            "waveform": recent_data[-5000:].tolist(),  # 发送最近 5000ms 波形
            "highlight_range": [4000, 5000]  # 高亮最近 1s 数据
        }))
        print('[INFO] send class', predicted_class)

    async def disconnect(self, close_code):
        print("[INFO] WebSocket 断开")
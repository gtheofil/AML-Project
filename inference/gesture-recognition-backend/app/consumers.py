import json
import numpy as np
from collections import deque
from channels.generic.websocket import AsyncWebsocketConsumer
from tensorflow.keras.models import load_model

# 加载 LSTM 预测模型
MODEL_PATH = r"E:\MSC\Spring\AML\GestureLink\new_collect\fzh\cnn_emg_model.h5"
model = load_model(MODEL_PATH)

# **全局变量**
data_buffer = deque(maxlen=5000)  # 5s 缓存
TIME_STEPS = 100  # LSTM 输入时间步长
STRIDE = 50  # 滑动窗口步长
NUM_WINDOWS = 19  # 5s 数据滑动后 19 个窗口
NUM_CHANNELS = 10  # 4 EMG + 6 IMU

class GestureRecognitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("[INFO] WebSocket 连接已建立")

    async def receive(self, text_data):
        """ 接收 Arduino 传感器数据, 存入 buffer """
        data = json.loads(text_data)

        try:
            # 解析数据
            emg_values = list(map(int, data["emg"]))  # 4 通道 EMG
            imu_values = list(map(int, data["acc"] + data["gyro"]))  # 6 轴 IMU

            if len(emg_values) == 4 and len(imu_values) == 6:
                # 存入缓存
                data_buffer.append(emg_values + imu_values)

            # 仅每 500ms 运行一次预测
            if len(data_buffer) >= 5000 and len(data_buffer) % 500 == 0:
                await self.run_prediction()

        except Exception as e:
            print(f"[ERROR] 数据解析失败: {e}")

    async def run_prediction(self):
        """ 读取最近 5s 数据，滑动窗口化，并进行预测 """
        if len(data_buffer) < 5000:
            return

        # 获取最近 5s 数据
        recent_data = list(data_buffer)[-5000:]
        data_array = np.array(recent_data)# (5000, 10)

        # 滑动窗口处理
        windows = []
        for start in range(0, 5000 - TIME_STEPS + 1, STRIDE):
            windows.append(data_array[start:start + TIME_STEPS])  # (100, 10)

        # 转换形状 (1, 19, 1000)
        processed_windows = np.array(windows).reshape(1, NUM_WINDOWS, TIME_STEPS * NUM_CHANNELS)

        # 运行预测
        predictions = model.predict(processed_windows, verbose=0)
        predicted_class = int(np.argmax(predictions, axis=1))

        # 发送分类结果 & 波形
        await self.send(json.dumps({
            "gesture": predicted_class,
            "waveform": recent_data[-5000:],  # 发送最近 5000ms 波形
            "highlight_range": [4000, 5000]  # 高亮最近 1s 数据
        }))

    async def disconnect(self, close_code):
        print("[INFO] WebSocket 断开")

import json
import numpy as np
import asyncio
from collections import deque
from channels.generic.websocket import AsyncWebsocketConsumer
from tensorflow.keras.models import load_model
from sklearn.preprocessing import StandardScaler
import random

# 加载 LSTM 预测模型
MODEL_PATH = r"E:\MSC\Spring\AML\GestureLink\weights\cnn_emg_model_all_channels.h5"
model = load_model(MODEL_PATH)

# **全局变量**
data_buffer = deque(maxlen=5000)  # 5秒数据缓存
TIME_STEPS = 100  # LSTM 输入时间步长
STRIDE = 250  # 计算滑动窗口步长
NUM_CHANNELS = 10  # 4 EMG + 6 IMU
NUM_WINDOWS = (5000 - TIME_STEPS) // STRIDE + 1  # 计算窗口数量
scaler = StandardScaler()

class GestureRecognitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        print("[INFO] WebSocket 连接已建立")
        self.running = True
        # 模拟数据每 0.5 秒发送一次
        asyncio.create_task(self.simulate_data())
        # 定期发送预测
        asyncio.create_task(self.send_periodic_predictions())
        # asyncio.create_task(self.run_prediction())

    async def simulate_data(self):
        """ 模拟接收随机生成的数据并存入缓冲区 """
        while self.running:
            # 模拟随机生成数据
            gesture_data = {
                "emg": [random.randint(100, 1000) for _ in range(4)],  # 随机生成 4 通道 EMG 数据
                "acc": [random.randint(-10000, 10000) for _ in range(3)],  # 随机生成 3 轴加速度数据
                "gyro": [random.randint(-10000, 10000) for _ in range(3)]  # 随机生成 3 轴陀螺仪数据
            }
            # 将数据添加到缓冲区
            data_buffer.append(gesture_data["emg"] + gesture_data["acc"] + gesture_data["gyro"])
            # print(f"[INFO] 模拟数据: {gesture_data}")
            await asyncio.sleep(0.001)  # 每 0.5 秒模拟发送一次数据

    async def receive(self, text_data=None):
        """ 模拟接收 Arduino 传感器数据, 存入 buffer """
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
        """ 每 0.5 秒进行一次预测并发送数据 """
        while self.running:
            if len(data_buffer) >= 500:  # 减少阈值以加速测试
                await self.run_prediction()
            await asyncio.sleep(0.5)

    async def run_prediction(self):
        """ 读取最近 5s 数据，滑动窗口化，并进行预测 """
        if len(data_buffer) < 5000:
            print("[WARNING] 数据不足 5s, 无法进行预测",len(data_buffer))
            return

        # 获取最近 5s 数据
        recent_data = np.array(list(data_buffer)[-5000:])  # (5000, 10)
        scaled_data = scaler.fit_transform(recent_data)  # 归一化

        # 滑动窗口处理
        windows = []
        for start in range(0, 5000 - TIME_STEPS + 1, STRIDE):
            if start + TIME_STEPS <= len(scaled_data):  # 确保不会越界
                windows.append(scaled_data[start:start + TIME_STEPS].flatten())

        # 转换成 NumPy 数组
        windows_array = np.array(windows)
        windows_array = windows_array[:19,:]
        # print(f"[DEBUG] 滑动窗口 shape: {windows_array.shape}")

        # 确保形状匹配
        expected_shape = (NUM_WINDOWS, TIME_STEPS * NUM_CHANNELS)

        # 进行 reshape
        try:
            processed_windows = windows_array.reshape(1, 19, TIME_STEPS * NUM_CHANNELS)
        except ValueError as e:
            print(f"[ERROR] 维度错误: {e}, windows.shape={windows_array.shape}")
            return

        # 运行预测
        predictions = model.predict(processed_windows, verbose=0)
        predicted_class = int(np.argmax(predictions, axis=1))

        print(f"[DEBUG] 预测结果: {predicted_class}")

        # 发送分类结果 & 波形
        try:
            await self.send(json.dumps({
                "gesture": predicted_class,
                "waveform": recent_data[-5000:].transpose().tolist(),  # 发送最近 5000ms 波形
                "highlight_range": [4000, 5000]  # 高亮最近 1s 数据
            }))
            print(f'send class: {predicted_class}')
        except Exception as e:
            print(f"[ERROR] WebSocket 发送失败: {e}")

    async def disconnect(self, close_code):
        print("[INFO] WebSocket 断开")
        self.running = False

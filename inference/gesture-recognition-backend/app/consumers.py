import json
import numpy as np
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class GestureRecognitionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """ 连接 WebSocket """
        await self.accept()
        print("[DEBUG] WebSocket 已连接")
        self.running = True
        asyncio.create_task(self.send_fake_data())  # 启动数据发送任务

    async def send_fake_data(self):
        """ 每 1 秒发送固定的 Gesture: 19 和随机波形 """
        while self.running:
            try:
                fake_waveform = np.random.randint(0, 1000, size=(5000, 10)).tolist()  # 生成 5000ms 的波形数据
                await self.send(json.dumps({
                    "gesture": 19,  # 固定手势类
                    "waveform": fake_waveform,
                    "highlight_range": [4000, 5000]  # 高亮最近 1s 数据
                }))
                await asyncio.sleep(3) 
                await self.send(json.dumps({
                    "gesture": 20,  # 固定手势类
                    "waveform": fake_waveform,
                    "highlight_range": [4000, 5000]  # 高亮最近 1s 数据
                }))
                await asyncio.sleep(3) 
                await self.send(json.dumps({
                    "gesture": 21,  # 固定手势类
                    "waveform": fake_waveform,
                    "highlight_range": [4000, 5000]  # 高亮最近 1s 数据
                }))
                print("[DEBUG] 发送 class 19 和随机波形数据")
                await asyncio.sleep(3)  # 每秒发送一次
            except Exception as e:
                print(f"[ERROR] 发送数据失败: {e}")

    async def receive(self, text_data):
        """ 仅用于测试，不处理数据 """
        print("[DEBUG] 收到前端消息:", text_data)

    async def disconnect(self, close_code):
        """ 断开 WebSocket 连接 """
        print("[DEBUG] WebSocket 断开")
        self.running = False  # 结束发送任务

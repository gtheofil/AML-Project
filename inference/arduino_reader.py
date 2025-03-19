import serial
import json
import asyncio
import websockets

# 配置 Arduino 串口
SERIAL_PORT = "COM3"  # 修改为你的 Arduino 端口
BAUD_RATE = 115200

# 连接串口
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

async def send_data():
    async with websockets.connect("ws://localhost:8000/ws/gesture/") as websocket:
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                parts = line.split()
                if len(parts) == 10:  # 确保数据完整
                    try:
                        data = {
                            "emg": list(map(int, parts[:4])),   # EMG 数据 (4通道)
                            "acc": list(map(int, parts[4:7])),  # 加速度 (X, Y, Z)
                            "gyro": list(map(int, parts[7:]))   # 角速度 (X, Y, Z)
                        }

                        # 发送数据到 WebSocket
                        await websocket.send(json.dumps(data))
                        print(f"[INFO] 发送数据: {data}")

                    except ValueError:
                        print(f"[WARNING] 数据解析失败: {line}")

asyncio.run(send_data())

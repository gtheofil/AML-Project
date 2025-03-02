import serial
import json
import asyncio
import websockets

# 1. 配置串口
ser = serial.Serial('COM3', 115200, timeout=1)

async def send_data():
    async with websockets.connect("ws://localhost:8000/ws/arduino/") as websocket:
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                parts = line.split()
                if len(parts) == 7:
                    try:
                        data = {
                            "emg": int(parts[0]),
                            "acc": [int(parts[1]), int(parts[2]), int(parts[3])],
                            "gyro": [int(parts[4]), int(parts[5]), int(parts[6])]
                        }
                        await websocket.send(json.dumps(data))
                        print(f"Sent: {data}")  # 终端调试
                    except ValueError:
                        print(f"Invalid data received: {line}")

asyncio.run(send_data())

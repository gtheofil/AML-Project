import serial
import csv
from datetime import datetime

# 设置串口（Windows 例子：COM3，Linux/Mac：/dev/ttyUSB0）
ser = serial.Serial('COM3', 115200)  # 修改为你的 Arduino 端口
# ser = serial.Serial('/dev/ttyUSB0', 115200)  # Linux / Mac

# 生成 CSV 文件
filename = f"emg_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Time (ms)", "EMG1", "EMG2", "EMG3", "EMG4"])  # 写入表头

    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            parts = line.split(",")
            
            if len(parts) == 5:  # 确保数据完整
                timestamp, emg1, emg2, emg3, emg4 = parts
                writer.writerow([timestamp, emg1, emg2, emg3, emg4])
                print(f"Time: {timestamp} ms | EMG1: {emg1} | EMG2: {emg2} | EMG3: {emg3} | EMG4: {emg4}")

        except KeyboardInterrupt:
            print("\n数据采集结束")
            break

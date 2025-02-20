import serial
import csv
from datetime import datetime

# 设置串口参数
ser = serial.Serial('COM9', 115200, timeout=1)

# 生成 CSV 文件名
filename = f"emg_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Time (ms)", "EMG Value"])  # CSV 头部
    
    start_time = datetime.now()

    try:
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:  # 确保数据不为空
                parts = line.split()  # 按空格拆分数据
                if len(parts) == 1:  # 只有当数据完整时才处理
                    try:
                        emg_value = int(parts[0])  # 解析第三个数值 (sensorValue)
                        elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # 计算时间(ms)

                        # 写入 CSV
                        writer.writerow([elapsed_time, emg_value])
                        print(f"Time: {elapsed_time:.2f} ms, EMG: {emg_value}")
                    except ValueError:
                        print(f"无法解析的行: {line}")  # 遇到异常数据，跳过
    except KeyboardInterrupt:
        print("数据采集结束")
    finally:
        ser.close()  # 释放串口

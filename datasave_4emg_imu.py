import os
import serial
import csv
from datetime import datetime

# 配置串口
ser = serial.Serial('COM4', 115200, timeout=1)

# 创建数据文件夹
data_dir = r"data\G"
os.makedirs(data_dir, exist_ok=True)

# 找到最新的文件编号
existing_files = [f for f in os.listdir(data_dir) if f.startswith("sensor_data") and f.endswith(".csv")]
file_numbers = [int(f[12:-4]) for f in existing_files if f[12:-4].isdigit()]
next_file_number = max(file_numbers, default=0) + 1

# 生成新的 CSV 文件名
filename = os.path.join(data_dir, f"sensor_data{next_file_number}.csv")

with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # 写入 CSV 头部
    writer.writerow(["Time (ms)", "EMG1", "EMG2", "EMG3", "EMG4", "AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"])

    start_time = datetime.now()

    try:
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                parts = line.split()  # 以空格分割数据
                if len(parts) == 10:  # 确保数据格式正确
                    try:
                        emg_values = list(map(int, parts[:4]))  # 解析 EMG 数据
                        imu_values = list(map(int, parts[4:]))  # 解析 IMU 数据
                        
                        elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # 计算时间（毫秒）

                        # 写入 CSV 文件
                        writer.writerow([elapsed_time] + emg_values + imu_values)

                        # 打印到控制台
                        print(f"Time: {elapsed_time:.2f} ms, EMG: {emg_values}, Acc: {imu_values[:3]}, Gyro: {imu_values[3:]}")
                    
                    except ValueError:
                        print(f"无效数据: {line}")  # 处理非整数值
    except KeyboardInterrupt:
        print("\n数据采集已停止。")
    finally:
        ser.close()  # 安全关闭串口

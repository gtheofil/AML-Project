import serial
import csv
from datetime import datetime

# **配置串口**
ser = serial.Serial('COM4', 115200, timeout=1)

# **生成 CSV 文件名**
filename = f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # **写入 CSV 头**
    writer.writerow(["Time (ms)", "EMG1", "EMG2", "AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"])

    start_time = datetime.now()

    try:
        while True:
            # **读取串口数据**
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                parts = line.split(' ')  # **按逗号分割数据**
                
                if len(parts) == 8:  # **确保数据完整（时间戳 + 8 个传感器数据）**
                    try:
                        # time_ms = float(parts[0].strip())  # **时间戳（浮点数）**
                        emg1_value = int(parts[0].strip())  # **第 1 个 EMG**
                        emg2_value = int(parts[1].strip())  # **第 2 个 EMG**
                        acc_x = int(parts[2].strip())
                        acc_y = int(parts[3].strip())
                        acc_z = int(parts[4].strip())
                        gyro_x = int(parts[5].strip())
                        gyro_y = int(parts[6].strip())
                        gyro_z = int(parts[7].strip())

                        elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # **计算相对时间 (ms)**

                        # **写入 CSV**
                        writer.writerow([elapsed_time, emg1_value, emg2_value, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z])

                        # **打印数据**
                        print(f"Time: {elapsed_time:.2f} ms, EMG1: {emg1_value}, EMG2: {emg2_value}, AccX: {acc_x}, AccY: {acc_y}, AccZ: {acc_z}, GyroX: {gyro_x}, GyroY: {gyro_y}, GyroZ: {gyro_z}")
                    
                    except ValueError:
                        print(f"Invalid data received: {line}")  # **非数值数据**
    except KeyboardInterrupt:
        print("\nData collection stopped by user.")
    finally:
        ser.close()  # **关闭串口**

import serial
import csv
from datetime import datetime

# Configure the serial port
ser = serial.Serial('COM4', 115200, timeout=1)

# Generate CSV filename
filename = f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Write CSV header
    writer.writerow(["Time (ms)", "EMG1", "EMG2","EMG3","EMG4","AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"])

    start_time = datetime.now()

    try:
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                parts = line.split()  # Split data by spaces
                if len(parts) == 10:  # Ensure correct data format (EMG + 6 IMU values)
                    try:
                        emg_value1 = int(parts[0])  # First value is EMG
                        emg_value2 = int(parts[1])
                        emg_value3 = int(parts[2])
                        emg_value4 = int(parts[3])
                        acc_x = int(parts[4])
                        acc_y = int(parts[5])
                        acc_z = int(parts[6])
                        gyro_x = int(parts[7])
                        gyro_y = int(parts[8])
                        gyro_z = int(parts[9])
                        
                        elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # Time in ms

                        # Write data to CSV
                        writer.writerow([elapsed_time, emg_value1, emg_value2, emg_value3, emg_value4, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z])

                        # Print to console
                        print(f"Time: {elapsed_time:.2f} ms, EMG1: {emg_value1}, EMG2: {emg_value2},EMG3: {emg_value3}, EMG4: {emg_value4}, AccX: {acc_x}, AccY: {acc_y}, AccZ: {acc_z}, GyroX: {gyro_x}, GyroY: {gyro_y}, GyroZ: {gyro_z}")
                    
                    except ValueError:
                        print(f"Invalid data received: {line}")  # Handle non-integer values
    except KeyboardInterrupt:
        print("\nData collection stopped by user.")
    finally:
        ser.close()  # Close the serial port safely

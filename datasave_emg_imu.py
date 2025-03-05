import serial
import csv
from datetime import datetime

# Configure the serial port
ser = serial.Serial('COM3', 115200, timeout=1)

# Generate CSV filename
filename = f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Write CSV header
    writer.writerow(["Time (ms)", "EMG", "AccX", "AccY", "AccZ", "GyroX", "GyroY", "GyroZ"])

    start_time = datetime.now()

    try:
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line:
                parts = line.split()  # Split data by spaces
                if len(parts) == 7:  # Ensure correct data format (EMG + 6 IMU values)
                    try:
                        emg_value = int(parts[0])  # First value is EMG
                        acc_x = int(parts[1])
                        acc_y = int(parts[2])
                        acc_z = int(parts[3])
                        gyro_x = int(parts[4])
                        gyro_y = int(parts[5])
                        gyro_z = int(parts[6])
                        
                        elapsed_time = (datetime.now() - start_time).total_seconds() * 1000  # Time in ms

                        # Write data to CSV
                        writer.writerow([elapsed_time, emg_value, acc_x, acc_y, acc_z, gyro_x, gyro_y, gyro_z])

                        # Print to console
                        print(f"Time: {elapsed_time:.2f} ms, EMG: {emg_value}, AccX: {acc_x}, AccY: {acc_y}, AccZ: {acc_z}, GyroX: {gyro_x}, GyroY: {gyro_y}, GyroZ: {gyro_z}")
                    
                    except ValueError:
                        print(f"Invalid data received: {line}")  # Handle non-integer values
    except KeyboardInterrupt:
        print("\nData collection stopped by user.")
    finally:
        ser.close()  # Close the serial port safely

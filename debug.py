import serial

ser = serial.Serial('COM9', 115200, timeout=1)

while True:
    raw_data = ser.readline()  # 读取一行
    print("Raw Bytes:", raw_data)  # 打印原始二进制数据
    try:
        decoded = raw_data.decode('utf-8')  # 试图解码
        print("Decoded:", decoded)
    except UnicodeDecodeError as e:
        print("解码失败:", e)

#include <TimerOne.h>
#include <Wire.h>

// MPU6050 I2C addresses
const int MPU6050_addr1 = 0x68;
const int MPU6050_addr2 = 0x69;

// IMU sensor data
volatile int16_t AccX1, AccY1, AccZ1, GyroX1, GyroY1, GyroZ1;
volatile int16_t AccX2, AccY2, AccZ2, GyroX2, GyroY2, GyroZ2;

// EMG data
volatile int emgValue1 = 0;
volatile int emgValue2 = 0;
volatile int emgValue3 = 0;
volatile int emgValue4 = 0;

// Timer flag
volatile bool dataReadyFlag = false;

void sampleData() {
  // Read EMG sensors
  emgValue1 = analogRead(A0);
  emgValue2 = analogRead(A1);
  emgValue3 = analogRead(A2);
  emgValue4 = analogRead(A3);

  // Read IMU data
  readMPU6050(MPU6050_addr1, AccX1, AccY1, AccZ1, GyroX1, GyroY1, GyroZ1);
  readMPU6050(MPU6050_addr2, AccX2, AccY2, AccZ2, GyroX2, GyroY2, GyroZ2);

  dataReadyFlag = true;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Initialize both MPU6050 sensors
  Wire.beginTransmission(MPU6050_addr1);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  Wire.beginTransmission(MPU6050_addr2);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  // Set Timer1 for 200 Hz (5000 µs interval)
  Timer1.initialize(5000);
  Timer1.attachInterrupt(sampleData);
}

void readMPU6050(int addr, int16_t &AccX, int16_t &AccY, int16_t &AccZ, int16_t &GyroX, int16_t &GyroY, int16_t &GyroZ) {
  Wire.beginTransmission(addr);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(addr, 14, true);

  AccX = Wire.read() << 8 | Wire.read();
  AccY = Wire.read() << 8 | Wire.read();
  AccZ = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read(); // Skip temperature data
  GyroX = Wire.read() << 8 | Wire.read();
  GyroY = Wire.read() << 8 | Wire.read();
  GyroZ = Wire.read() << 8 | Wire.read();
}

void loop() {
  if (dataReadyFlag) {
    noInterrupts();
    int emgCopy1 = emgValue1;
    int emgCopy2 = emgValue2;
    int emgCopy3 = emgValue3;
    int emgCopy4 = emgValue4;
    dataReadyFlag = false;
    interrupts();

    Serial.print(emgCopy1); Serial.print(" ");
    Serial.print(emgCopy2); Serial.print(" ");
    Serial.print(emgCopy3); Serial.print(" ");
    Serial.print(emgCopy4); Serial.print(" ");
    Serial.print(AccX1); Serial.print(" ");
    Serial.print(AccY1); Serial.print(" ");
    Serial.print(AccZ1); Serial.print(" ");
    Serial.print(GyroX1); Serial.print(" ");
    Serial.print(GyroY1); Serial.print(" ");
    Serial.print(GyroZ1); Serial.print(" ");
    Serial.print(AccX2); Serial.print(" ");
    Serial.print(AccY2); Serial.print(" ");
    Serial.print(AccZ2); Serial.print(" ");
    Serial.print(GyroX2); Serial.print(" ");
    Serial.print(GyroY2); Serial.print(" ");
    Serial.println(GyroZ2);
  }
}

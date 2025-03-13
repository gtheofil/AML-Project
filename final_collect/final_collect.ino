#include <TimerOne.h>
#include <Wire.h>

// MPU6050 I2C address
const int MPU6050_addr = 0x69;

// IMU sensor data
volatile int16_t AccX, AccY, AccZ, GyroX, GyroY, GyroZ;

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
  Wire.beginTransmission(MPU6050_addr);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU6050_addr, 14, true);

  AccX = Wire.read() << 8 | Wire.read();
  AccY = Wire.read() << 8 | Wire.read();
  AccZ = Wire.read() << 8 | Wire.read();
  Wire.read(); Wire.read(); // Skip temperature data
  GyroX = Wire.read() << 8 | Wire.read();
  GyroY = Wire.read() << 8 | Wire.read();
  GyroZ = Wire.read() << 8 | Wire.read();

  dataReadyFlag = true;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Initialize MPU6050
  Wire.beginTransmission(MPU6050_addr);
  Wire.write(0x6B);
  Wire.write(0);
  Wire.endTransmission(true);

  // Set Timer1 for 200 Hz (5000 µs interval)
  Timer1.initialize(5000);
  Timer1.attachInterrupt(sampleData);
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
    Serial.print(AccX); Serial.print(" ");
    Serial.print(AccY); Serial.print(" ");
    Serial.print(AccZ); Serial.print(" ");
    Serial.print(GyroX); Serial.print(" ");
    Serial.print(GyroY); Serial.print(" ");
    Serial.println(GyroZ);
  }
}
#include <TimerOne.h>
#include <Wire.h>

// MPU6050 I2C address
const int MPU6050_addr = 0x69;

// IMU sensor data
volatile int16_t AccX, AccY, AccZ, GyroX, GyroY, GyroZ;

// EMG data
volatile int emgValue = 0;

// Flag to trigger IMU reading in loop
volatile bool imuReadFlag = false;

// Timer1 ISR (Interrupt Service Routine) for EMG sampling
void sampleEMG() {
  emgValue = analogRead(A0); // Read EMG sensor at 2000 Hz

  // Set flag every 40 cycles (50 Hz IMU reading)
  static int counter = 0;
  counter++;
  if (counter >= 40) { // 40 * 500µs = 20ms (50 Hz)
    counter = 0;
    imuReadFlag = true; // Set flag for IMU reading
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  // Initialize MPU6050
  Wire.beginTransmission(MPU6050_addr);
  Wire.write(0x6B); // Power management register
  Wire.write(0);    // Wake up the MPU6050
  Wire.endTransmission(true);

  // Set Timer1 for EMG sampling at 2000 Hz (every 500 µs)
  Timer1.initialize(500);
  Timer1.attachInterrupt(sampleEMG);
}

void loop() {
  // Copy volatile EMG value safely
  noInterrupts();
  int emgCopy = emgValue;
  bool imuReady = imuReadFlag;
  imuReadFlag = false; // Reset flag
  interrupts();

  // Read MPU6050 data **only when the flag is set**
  if (imuReady) {
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
  }

  // Print EMG & IMU data to Serial
  Serial.print(emgCopy);
  Serial.print(" ");
  Serial.print(AccX); Serial.print(" ");
  Serial.print(AccY); Serial.print(" ");
  Serial.print(AccZ); Serial.print(" ");
  Serial.print(GyroX); Serial.print(" ");
  Serial.print(GyroY); Serial.print(" ");
  Serial.println(GyroZ);
}

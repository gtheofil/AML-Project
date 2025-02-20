#include <TimerOne.h>

void setup() {
  Serial.begin(115200); // 提高波特率，减少传输延迟
  Timer1.initialize(500); // 设置定时器中断，500微秒 = 2000Hz 采样率
  Timer1.attachInterrupt(sampleEMG);
}

void sampleEMG() {
  int sensorValue = analogRead(A0);
  
  // 发送数据到 Serial
  // Serial.print(0); 
  // Serial.print(" ");
  // Serial.print(1000); 
  // Serial.print(" ");
  Serial.println(sensorValue);
}


void loop() {
  // loop 为空，因为采样由定时器中断完成
}

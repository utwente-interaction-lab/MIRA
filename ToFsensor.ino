#include <Wire.h>
#include <VL53L1X.h>

VL53L1X sensor;

void setup() {
  Serial.begin(9600);
  Wire.begin();
  
  sensor.setTimeout(500);

  if (!sensor.init()) {
    Serial.println("Failed to detect and initialize sensor!");
    while (1);
  }

  sensor.setDistanceMode(VL53L1X::Long);  // Long-range mode
  sensor.setMeasurementTimingBudget(50000);  // Timing budget
  sensor.startContinuous(50);  // Start continuous ranging
}

void loop() {
  uint16_t distance = sensor.read();
  
  // Buffer to store the formatted string
  char buffer[5];  // 4 digits + null terminator

  // Format the integer with leading zeros (width of 4)
  sprintf(buffer, "%04d", distance);
  
  // Send the formatted string to Python
  Serial.println(buffer);
  
  delay(100);
}
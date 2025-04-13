#include <Wire.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"
#include "heartRate.h"
#include <WiFi.h>
#include <PubSubClient.h>

MAX30105 particleSensor;

// Constants for SpO2 calculation
#define BUFFER_SIZE 100

uint32_t irBuffer[BUFFER_SIZE]; // Infrared LED sensor data
uint32_t redBuffer[BUFFER_SIZE]; // Red LED sensor data
int32_t spo2;
int8_t validSPO2;
int32_t heartRate;
int8_t validHeartRate;

// WiFi and MQTT settings
const char* ssid = "Dialog 4G";         // Replace with your Wi-Fi SSID
const char* password = "4RNAJBYMBTF"; // Replace with your Wi-Fi password
const char* mqtt_server = "test.mosquitto.org"; // Public MQTT broker
const int mqtt_port = 1883;  // Default MQTT port (non-SSL)

WiFiClient espClient;
PubSubClient client(espClient);

// MQTT topic
const char* heartRateTopic = "navee/sensor/heartRate";
const char* spo2Topic = "navee/sensor/spo2";
const char* irValueTopic = "navee/sensor/irValue";

// Function to connect to Wi-Fi
void setup_wifi() {
  delay(10);
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("Connected to WiFi");
}

// Function to connect to MQTT broker
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    if (client.connect("ESP32Client")) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102 not found. Check wiring/power.");
    while (1);
  }

  particleSensor.setup(); // Use default settings
  particleSensor.setPulseAmplitudeRed(0x0A); // Low brightness
  particleSensor.setPulseAmplitudeIR(0x0A); // Low brightness
  
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  // Read 100 samples (at 100 Hz = ~1 sec)
  for (byte i = 0; i < BUFFER_SIZE; i++) {
    while (!particleSensor.available()) {
      particleSensor.check(); // Refresh sensor readings
    }

    redBuffer[i] = particleSensor.getRed();
    irBuffer[i] = particleSensor.getIR();
    particleSensor.nextSample(); // Advance to next sample
  }

  // Calculate SpO2 and BPM
  maxim_heart_rate_and_oxygen_saturation(irBuffer, BUFFER_SIZE, redBuffer, 
                                         &spo2, &validSPO2, &heartRate, &validHeartRate);

  // Publish data if valid
  if (validHeartRate && validSPO2) {
    String heartRateStr = String(heartRate);
    String spo2Str = String(spo2);
    String irValueStr = String(irBuffer[BUFFER_SIZE - 1]);

    // Send to MQTT broker
    client.publish(heartRateTopic, heartRateStr.c_str());
    client.publish(spo2Topic, spo2Str.c_str());
    client.publish(irValueTopic, irValueStr.c_str());

    // Print to Serial Monitor
    Serial.print("💓 Heart Rate: ");
    Serial.print(heartRate);
    Serial.print(" BPM  |  ");
    Serial.print("🩸 SpO2: ");
    Serial.print(spo2);
    Serial.print(" %  |  ");
    Serial.print("IR Value: ");
    Serial.println(irBuffer[BUFFER_SIZE - 1]);
  } else {
    Serial.println("Reading...");
  }

  delay(1000); // Wait a second before the next reading
}

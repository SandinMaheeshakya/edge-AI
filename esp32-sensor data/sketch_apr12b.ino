#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <Wire.h>
#include "MAX30105.h"

// Wi-Fi credentials
const char* ssid = "Dialog 4G";
const char* password = "homeswee@home123AB";

// MQTT broker info
const char* mqtt_server = "192.168.8.100";
const int mqtt_port = 1883;
const char* mqtt_topic = "device/esp32_001";
const char* device_id = "esp32_001";

// DS18B20 sensor on GPIO4
#define ONE_WIRE_BUS 4
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// MAX30102 sensor
MAX30105 particleSensor;

// MQTT setup
WiFiClient espClient;
PubSubClient client(espClient);

// Wi-Fi connect
void setup_wifi() {
  delay(100);
  Serial.print("Connecting to ");
  Serial.println(ssid);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
}

// Reconnect MQTT
void reconnect() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    if (client.connect(device_id)) {
      Serial.println("connected");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds...");
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, mqtt_port);

  // Start DS18B20
  sensors.begin();

  // Initialize MAX30102
  Wire.begin();  
  if (!particleSensor.begin(Wire, I2C_SPEED_STANDARD)) {
    Serial.println("MAX30102 not found. Check wiring!");
    while (1);
  }

  particleSensor.setup(); 
  particleSensor.setPulseAmplitudeRed(0x0A); 
  particleSensor.setPulseAmplitudeIR(0x0A);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  // Get temperature from DS18B20
  sensors.requestTemperatures();
  float temperature = sensors.getTempCByIndex(0);

  // Get readings from MAX30102
  long irValue = particleSensor.getIR();
  long redValue = particleSensor.getRed();

  // Simple SpO2 and heart rate estimation logic
  int heartRate = map(redValue % 1000, 0, 999, 60, 100);
  int spo2 = map(irValue % 1000, 0, 999, 95, 100);

  // Build JSON payload
  StaticJsonDocument<256> doc;
  doc["device_id"] = device_id;
  doc["temperature"] = temperature;
  doc["heart_rate"] = heartRate;
  doc["oxygen_saturation"] = spo2;
  doc["ir_value"] = irValue;

  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);
  client.publish(mqtt_topic, jsonBuffer);

  // Print to Serial Monitor
  Serial.println("Sent to MQTT:");
  Serial.println(jsonBuffer);

  delay(1000);
}

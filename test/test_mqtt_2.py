import paho.mqtt.publish as publish
import json
import time
import random

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/data/#"  # Replace testdevice001 with a test ID

# Sample payload
payload = {
    "device_id": 'esp32_002' ,
    "temperature":round(random.uniform(36.0, 38.5), 2),
    "oxygen_saturation": random.randint(90, 100),
    "heart_rate": random.randint(60, 100),
    "ir_value": random.randint(50000, 100000)

}

while True:
    publish.single(
        MQTT_TOPIC,
        payload=json.dumps(payload),
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
    print(f"Published to {MQTT_TOPIC}: {payload}")
    time.sleep(5)  # publish every 5 seconds

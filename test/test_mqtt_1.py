import paho.mqtt.publish as publish
import json
import time
import random

MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/data/esp32_001"  # Replace testdevice001 with a test ID

# Sample payload
def generate_payload():

    payload = {
        "device_id": 'esp32_001' ,
        "temperature":round(random.uniform(36.0, 38.5), 2),
        "oxygen_saturation": random.randint(90, 100),
        "heart_rate": random.randint(60, 100),
        "ir_value": random.randint(50000, 100000)

    }

    return payload

while True:

    payload = generate_payload()
    publish.single(
        MQTT_TOPIC,
        payload=json.dumps(payload),
        hostname=MQTT_BROKER,
        port=MQTT_PORT
    )
    print(f"Published to {MQTT_TOPIC}: {payload}")

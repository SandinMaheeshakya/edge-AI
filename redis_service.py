import redis
import paho.mqtt.client as mqtt
import json

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# MQTT Callback
def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    print(f"Received: {payload}")
    r.rpush("sensor_queue", payload)  # Store in Redis queue

# Set up MQTT
client = mqtt.Client()
client.on_message = on_message
client.connect("mqtt.eclipseprojects.io", 1883)  # Use a free broker or local broker
client.subscribe("sensor/data")
client.loop_forever()

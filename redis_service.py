import json
import redis
import paho.mqtt.client as mqtt
import time
import pandas as pd
import logging
import colorlog
import os
from dotenv import load_dotenv

# Script Configuration
# .env file load
BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, '.env'),override=True)

"""Logger Configurations"""

formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",  # Format
    datefmt="%Y-%m-%d %H:%M:%S",
    reset=True,  
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'light_green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    },
    secondary_log_colors={},
    style='%'
)

console_handler = colorlog.StreamHandler()
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler(os.getenv("REDIS_LOG"))
file_handler.setFormatter(logging.Formatter(os.getenv("LOGGING_FORMAT")))

# Configure logging with both handlers
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)

logger = logging.getLogger(__name__)

# Connect to Redis
redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"))

# MQTT settings
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PORT = int(os.getenv("MQTT_PORT"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC")

def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic_parts = msg.topic.split('/')

        # Try getting device_id from payload or topic
        device_id = payload.get('device_id') or topic_parts[-1]
        ir_value  = payload.get('ir_value')
        temperature = payload.get('temperature')
        oxygen_rate = payload.get('oxygen_saturation')
        heart_rate = payload.get('heart_rate')

        timestamp = str(pd.Timestamp.now())
        
        # Store the latest reading
        redis_client.hset(f'esp32:{device_id}:latest', mapping={
            'device_id' : device_id,
            'ir_value' : ir_value,
            'temperature': temperature,
            'oxygen_saturation': oxygen_rate,
            'heart_rate': heart_rate,
            'timestamp': timestamp
        })

        # Store time-series data
        redis_client.rpush(f'esp32:{device_id}:history', json.dumps({
            'device_id' : device_id,
            'ir_value' : ir_value,
            'timestamp': timestamp,
            'temperature': temperature,
            'oxygen_saturation': oxygen_rate,
            'heart_rate': heart_rate
        }))

        print(f"[{device_id}] Data saved at {timestamp}")

    except Exception as e:
        print(f"[{msg.topic}] Error: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()

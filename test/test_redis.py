import redis
import json
import time
import random
import pandas as pd

# Redis connection setup
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Simulated device ID
device_id = "esp32_001"

def generate_fake_data():
    """Generate random sensor data."""
    return {
        "device_id" : device_id,
        "temperature": round(random.uniform(36.0, 38.5), 2),
        "oxygen_rate": random.randint(90, 100),
        "heart_rate": random.randint(60, 100),
        "timestamp": str(pd.Timestamp.now())
    }

def insert_to_redis(device_id, data):
    # Latest reading hash
    redis_client.hset(f'esp32:{device_id}:latest', mapping=data)

    # Time-series history list
    redis_client.rpush(f'esp32:{device_id}:history', json.dumps(data))

    print(f"[{device_id}] Inserted data at {data['timestamp']}")
    print(json.dumps(data, indent=2))

if __name__ == "__main__":
    for _ in range(5):  # Insert 5 sample entries
        time.sleep(10)
        data = generate_fake_data()
        insert_to_redis(device_id, data)
        time.sleep(1)

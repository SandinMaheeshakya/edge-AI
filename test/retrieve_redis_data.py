import redis
import json
import pandas as pd

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Device ID to fetch data for
device_id = "esp32_001"

# Redis keys
latest_key = f'esp32:{device_id}:latest'
history_key = f'esp32:{device_id}:history'

# Fetch latest reading
latest_data = redis_client.hgetall(latest_key)

print(f"\n🔹 Latest Data for {device_id}:")
if latest_data:
    for k, v in latest_data.items():
        print(f"{k.decode()}: {v.decode()}")
else:
    print("No latest data found.")

# Fetch history
history = redis_client.lrange(history_key, -5, -1)

print(f"\n📜 History Data for {device_id}:")
if history:
    parsed_history = [json.loads(item.decode('utf-8')) for item in history]
    df = pd.DataFrame(parsed_history)

    print(df)

    keys = redis_client.keys('esp32:*:latest')
    distinct_ids = set()

    for key in keys:
        # Decode if necessary (for Python 3 / redis-py)
        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
        
        # Extract the device_id from 'esp32:{device_id}:latest'
        parts = key_str.split(':')
        if len(parts) == 3:
            distinct_ids.add(parts[1])

        print(distinct_ids)

else:
    print("No history data found.")

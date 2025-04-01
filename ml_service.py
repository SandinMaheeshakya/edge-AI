import redis
import json
import numpy as np
import boto3

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Set up AWS S3
s3 = boto3.client('s3', aws_access_key_id="YOUR_ACCESS_KEY", aws_secret_access_key="YOUR_SECRET_KEY")
BUCKET_NAME = "your-s3-bucket"

# Load TensorFlow Lite Model
interpreter = tflite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

def process_data(sensor_value):
    input_data = np.array([sensor_value], dtype=np.float32).reshape(1, 1)
    interpreter.set_tensor(interpreter.get_input_details()[0]['index'], input_data)
    interpreter.invoke()
    output_data = interpreter.get_tensor(interpreter.get_output_details()[0]['index'])
    return float(output_data[0][0])

while True:
    data = r.lpop("sensor_queue")  # Fetch data from Redis queue
    if data:
        sensor_data = json.loads(data)
        prediction = process_data(sensor_data["value"])

        # Upload to S3
        s3.put_object(Body=json.dumps({"sensor_value": sensor_data["value"], "prediction": prediction}), Bucket=BUCKET_NAME, Key="data.json")
        print(f"Processed and uploaded: {sensor_data['value']} -> {prediction}")

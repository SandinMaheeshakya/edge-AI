import pandas as pd
import joblib
import logging
import colorlog
import os
import boto3
import time
from io import StringIO
import redis
import json
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler

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
file_handler = logging.FileHandler(os.getenv("ML_SERVICE_LOG"))
file_handler.setFormatter(logging.Formatter(os.getenv("LOGGING_FORMAT")))

# Configure logging with both handlers
logging.basicConfig(
    level=logging.INFO,
    handlers=[console_handler, file_handler]
)

logger = logging.getLogger(__name__)

"""Model Configurations"""
health_classification_model = joblib.load(os.getenv("MODEL_PATH"))

"""Redis Configurations"""
redis_client = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"))

def get_current_active_devices():

    try:
        logger.info("Getting the current active devices")
        keys = redis_client.keys('esp32:*:latest')
        distinct_ids = set()

        for key in keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            parts = key_str.split(':')
            if len(parts) == 3:
                distinct_ids.add(parts[1])

        return distinct_ids

    except Exception as e:
        logger.error(f"Cannot get current active devices due to :- {e}")

        
def retrieve_redis_data(device_id):
    try:
        logger.info(f"Started retrieving information from Redis for the device id:- {device_id}")
        # Redis keys
        latest_key = f'esp32:{device_id}:latest'

        # Fetch latest reading
        latest_data = redis_client.hgetall(latest_key)
        
        if latest_data:
            logger.info(f"Sucessfully retrieved the latest health data for the device_id :- {device_id}")

        return latest_data

    except Exception as e:
        logger.error(f"Cannot retrieve redis data due to :- {e}")

def preprocess_data(retrieved_data):
    """This function processes the data coming through MQTT Broker"""
    try:
        logger.info("Starting the pre-process of MQTT Data")
        retrieved_data = [json.loads(item.decode('utf-8')) for item in retrieved_data]
        retrieved_df = pd.DataFrame(retrieved_data)

        # Standarizing the data
        scaler = MinMaxScaler()
        retrieved_df[['heart_rate', 'oxygen_saturation']] = scaler.fit_transform(retrieved_df[['heart_rate', 'oxygen_saturation']])

        return retrieved_df

    except Exception as e:
        logger.error(f"Cannot pre-process redis data due to :- {e}")
    

def run_health_classification_model(data,device_id):
    """
    This will load the health classification model and runs the health condition classification 
    for the patient

    Args:
        data (pd.DataFrame): Input data for prediction.

    Returns:
        int: Predicted class label.
    """
    try:
        logger.info(f"Health Classification Model Triggered at {pd.Timestamp.now()}")

        # Load the model
        # Predict
        prediction = health_classification_model.predict(data[['heart_rate', 'oxygen_saturation']])
        logger.info(f"Prediction: {prediction[0]}")
        
        if prediction[0] == 0:
            logger.info(f"Patient for the device_id :- {device_id} is currently Healthy!")
        
        elif prediction[0] == 1:
            logger.info(f"Patient for the device_id :- {device_id} is Not Healthy Please Checkup!")

        data['health_condition'] = prediction[0]

        return data

    except Exception as e:
        logger.error(f"Error in running Health Classification model: {e}")
        return None

def upload_data_s3(updated_df):
    try:
        logger.info("Starting insert data to S3 Bucket.")
        # Initialize S3 client
        s3 = boto3.client('s3')

        bucket_name = os.getenv("S3_BUCKET")
        file_key = os.getenv("CSV_FILE")

        try:
            obj = s3.get_object(Bucket = bucket_name, Key = file_key)
            existing_df = pd.read_csv(obj['Body'])

        except s3.exceptions.NoSuchKey:
            existing_df = pd.DataFrame()  # File doesn't exist yet

        updated_df = pd.concat([existing_df, updated_df], ignore_index=True)

        csv_buffer = StringIO()
        updated_df.to_csv(csv_buffer, index=False)

        s3.put_object(Bucket=bucket_name, Key=file_key, Body=csv_buffer.getvalue())
        
        logger.info("Sucessfully inserted data into S3 Bucket.")

    except Exception as e:
        logger.error(f"Cannot upload data to S3 due to :- {e}")

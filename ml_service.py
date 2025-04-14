import pandas as pd
import joblib
import logging
import colorlog
import os
import boto3
import time
from io import StringIO
import numpy as np
import tensorflow as tf
from scipy.signal import butter, filtfilt, find_peaks
import redis
import json
from dotenv import load_dotenv
from sklearn.preprocessing import MinMaxScaler

# Script Configuration
# .env file load
BASEDIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASEDIR, ".env"), override=True)

"""Logger Configurations"""
formatter = colorlog.ColoredFormatter(
    "%(log_color)s%(asctime)s - %(levelname)s - %(message)s",  # Format
    datefmt="%Y-%m-%d %H:%M:%S",
    reset=True,
    log_colors={
        "DEBUG": "cyan",
        "INFO": "light_green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    },
    secondary_log_colors={},
    style="%",
)

console_handler = colorlog.StreamHandler()
console_handler.setFormatter(formatter)
file_handler = logging.FileHandler(os.getenv("ML_SERVICE_LOG"))
file_handler.setFormatter(logging.Formatter(os.getenv("LOGGING_FORMAT")))

# Configure logging with both handlers
logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

logger = logging.getLogger(__name__)

"""Model Configurations"""
health_classification_model = joblib.load(os.getenv("MODEL_PATH"))
cvd_prediction_model_path = os.getenv("CVD_MODEL_PATH")

"""Redis Configurations"""
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB")
)

def get_current_active_devices():

    try:
        logger.info("Getting the current active devices")
        keys = redis_client.keys("esp32:*:latest")
        distinct_ids = set()

        for key in keys:
            key_str = key.decode("utf-8") if isinstance(key, bytes) else key
            parts = key_str.split(":")
            if len(parts) == 3:
                distinct_ids.add(parts[1])

        logger.info(f"Current Active Devices :- {distinct_ids}")
        return distinct_ids

    except Exception as e:
        logger.error(f"Cannot get current active devices due to :- {e}")


def retrieve_latest_redis_data(device_id):
    try:
        logger.info(
            f"Started retrieving information from Redis for the device id:- {device_id}"
        )
        # Redis keys
        latest_key = f"esp32:{device_id}:latest"

        # Fetch latest reading
        latest_data = redis_client.hgetall(latest_key)

        if latest_data:
            logger.info(
                f"Sucessfully retrieved the latest health data for the device_id :- {device_id}"
            )

            latest_data = {k.decode(): v.decode() for k, v in latest_data.items()}
            latest_data = [json.dumps(latest_data).encode("utf-8")]

            logger.info(f"latest data for the device id {device_id} :- {latest_data}")

        return latest_data

    except Exception as e:
        logger.error(f"Cannot retrieve redis data due to :- {e}")


# Helper function
def bandpass_filter(signal, fs, lowcut=0.1, highcut=0.5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(2, [low, high], btype="band")
    return filtfilt(b, a, signal)


def process_respiratory_rate(device_id, fs=100, lowcut=0.1, highcut=0.5):
    try:
        logger.info("Starts processing respiratory rate")
        logger.info("Retrieving the IR values for the last 10 seconds")

        # Retrieving the latest 10 seconds data for the each device
        history_key = f"esp32:{device_id}:history"
        history = redis_client.lrange(history_key, -10, -1)
        all_values = [json.loads(item) for item in history]
        ir_values = [item["ir_value"] for item in all_values]
        print(ir_values)
        ir_values = ir_values * fs
        ir_array = np.array(ir_values)
        filtered = bandpass_filter(ir_array, fs)
        peaks, _ = find_peaks(filtered, distance=fs * 1.5)
        duration_min = len(ir_array) / fs / 60
        rr = len(peaks) / duration_min
        logger.info(f"Estimated respiratory rate for the device id {device_id} :- {rr}")

        return rr

    except Exception as e:
        logger.error(
            f"Cannot execute the process_respiratory_rate function due to :- {e}"
        )

def preprocess_data(retrieved_data, device):
    """This function processes the data coming through MQTT Broker"""
    try:
        logger.info("Starting the pre-process of MQTT Data")
        retrieved_data = [json.loads(item.decode("utf-8")) for item in retrieved_data]
        retrieved_df = pd.DataFrame(retrieved_data)

        # Adding respiratory rate to the dataframe
        retrieved_df['respiratory_rate'] = process_respiratory_rate(device)
        retrieved_df.drop('ir_value',axis=1,inplace=True)

        # Standarizing the data
        """
        scaler = MinMaxScaler()
        retrieved_df[
            ["heart_rate", "oxygen_saturation", "temperature", "respiratory_rate"]
        ] = scaler.fit_transform(
            retrieved_df[
                ["heart_rate", "oxygen_saturation", "temperature", "respiratory_rate"]
            ]
        )
        """

        retrieved_df['heart_rate'] = 89
        retrieved_df['oxygen_saturation'] = 95
        retrieved_df['respiratory_rate'] = 16
        retrieved_df['temperature'] = 37.5 
        print(retrieved_df)

        logger.info("Sucessfully scaled the data.")

        logger.info(
            "Sucessfully pre-processed the data to feed into the ML and DL Models."
        )

        return retrieved_df

    except Exception as e:
        logger.error(f"Cannot pre-process redis data due to :- {e}")


def run_health_classification_model(data, device_id):
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
        health_condition_warning = False

        # Load the model
        # Predict
        prediction = health_classification_model.predict(
            data[["heart_rate", "oxygen_saturation"]]
        )
        logger.info(f"Prediction: {prediction[0]}")

        if prediction[0] == 0:
            logger.info(
                f"Patient for the device_id :- {device_id} is currently Healthy!"
            )

        elif prediction[0] == 1:
            logger.info(
                f"Patient for the device_id :- {device_id} is Not Healthy Please Checkup!"
            )

            health_condition_warning = True

        data["health_condition"] = prediction[0]
        data['health_condition_warning'] = health_condition_warning
        return data

    except Exception as e:
        logger.error(f"Error in running Health Classification model: {e}")
        return None

def run_cvd_classification_model(df:pd.DataFrame,device_id):

    try:
        logger.info(f"CVD Prediction Model Triggered at {pd.Timestamp.now()}")
        cvd_condition_warning = False

         # Load the TFLite model
        interpreter = tf.lite.Interpreter(model_path=cvd_prediction_model_path)
        interpreter.allocate_tensors()

        # input/output details
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()

        # Converting the Dataframe to match the model input
        input_shape = input_details[0]['shape']   
        input_dtype = input_details[0]['dtype']  

        input_data = df.drop(['device_id','health_condition','health_condition_warning','timestamp'],axis=1).to_numpy().astype(input_dtype).reshape(input_shape)

        # Run inference
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()
        output_data = interpreter.get_tensor(output_details[0]['index'])

        logger.info(f"Actual Output :- {output_data}")

        logger.info(f"Prediction: {int(output_data[0][0])}")

        if int(output_data[0][0]) == 0:

            logger.info(
                f"Patient for the device_id :- {device_id} is currently doesn't show any CVD condition"
            )

        elif int(output_data[0][0]) == 1:
            logger.info(
                f"Patient for the device_id :- {device_id} is showing CVD Symptoms! Please Check!!!"
            )

            cvd_condition_warning = True

        df["cvd_condition"] = int(output_data[0][0])
        df['cvd_condition_warning'] = cvd_condition_warning 

        return df

    except Exception as e:
        logger.error(f"Error in running Health Classification model: {e}")

def upload_data_s3(updated_df):
    try:
        logger.info("Starting insert data to S3 Bucket.")
        # Initialize S3 client
        s3 = boto3.client("s3")

        bucket_name = os.getenv("S3_BUCKET")
        file_key = os.getenv("CSV_FILE")

        try:
            obj = s3.get_object(Bucket=bucket_name, Key=file_key)
            existing_df = pd.read_csv(obj["Body"])

        except s3.exceptions.NoSuchKey:
            existing_df = pd.DataFrame()  # File doesn't exist yet

        updated_df = pd.concat([existing_df, updated_df], ignore_index=True)

        csv_buffer = StringIO()
        updated_df.to_csv(csv_buffer, index=False)

        s3.put_object(Bucket=bucket_name, Key=file_key, Body=csv_buffer.getvalue())

        logger.info("Sucessfully inserted data into S3 Bucket.")

    except Exception as e:
        logger.error(f"Cannot upload data to S3 due to :- {e}")


if __name__ == "__main__":
    active_devices = get_current_active_devices()

    while True:
        for device in active_devices:
            print(device)
            dataset = preprocess_data(retrieve_latest_redis_data(device),device)
            data_with_health_predictions = run_health_classification_model(
                dataset, device
            )
            print(data_with_health_predictions)
            data_with_cvd_predictions = run_cvd_classification_model(data_with_health_predictions,device)
            print(data_with_cvd_predictions)

        time.sleep(30)

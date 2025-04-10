import pandas as pd
import joblib
import logging
import colorlog
import os
import time
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


def run_health_classification_model(data,device_id):
    """
    This will load the SVC model and runs the health condition classification 
    for the patient

    Args:
        data (pd.DataFrame): Input data for prediction.

    Returns:
        int: Predicted class label.
    """
    
    try:
        logger.info(f"Health Classification Model Triggered at {pd.Timestamp.now()}")
        # Standarizing the data

        # Load the model
        # Predict
        prediction = health_classification_model.predict(data)
        logger.info(f"Prediction: {prediction[0]}")
        
        if prediction[0] == 0:
            logger.info(f"Patient for the device_id :- {device_id} is currently Healthy!")
        
        elif prediction[0] == 1:
            logger.info(f"Patient for the device_id :- {device_id} is Not Healthy Please Checkup!")

        return prediction[0]
    
    except Exception as e:
        logger.error(f"Error in running model: {e}")
        return None

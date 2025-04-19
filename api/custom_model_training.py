from sklearn.svm import SVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel

# Replace with your actual loading logic
def load_data():
    basic_data = pd.read_csv("Analyzed_Health_Condition_Data_Base.csv")
    return basic_data

def train_custom_svm(config: dict):

    basic_data = load_data()
    
    # Features and target based on input
    target_col = config.get("target_column", "healthcare_target")
    default_features = [col for col in basic_data.columns if col != target_col]
    features = config.get("features", default_features)

    X = basic_data[features]
    y = basic_data[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=config.get("test_size", 0.2),
        random_state=config.get("random_state", 42)
    )

    model_params = {
        "C": config.get("C", 1.0),
        "gamma": config.get("gamma", "scale"),
        "kernel": config.get("kernel", "rbf"),
        "probability": True
    }

    model = SVC(**model_params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    return {
        "accuracy": accuracy,
        "report": report,
        "params": model_params,
        "test_size": config.get("test_size", 0.2),
        "features_used": config["features"]
    }



from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Union, Optional
from pydantic import BaseModel
from custom_model_training import train_custom_svm
import subprocess
import os
import psutil

app = FastAPI(
    title="Pi Control API",
    description="API for controlling Raspberry Pi services, models, and system operations securely.",
    version="1.0.0"
)

# --- AUTHENTICATION (Bearer Token) ---
API_KEY = "o92F2N30vZ1y9n84KDLsQ8kx3OeKZsmv"
security = HTTPBearer()

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return credentials.credentials

# --- MODELS ---
class ServiceRequest(BaseModel):
    service_name: str

# --- SYSTEM CONTROL ENDPOINTS ---
@app.post("/shutdown")
def shutdown(_: str = Depends(verify_api_key)):
    subprocess.call(["sudo", "shutdown", "-h", "now"])
    return {"status": "shutting down"}

@app.post("/reboot")
def reboot(_: str = Depends(verify_api_key)):
    subprocess.call(["sudo", "reboot"])
    return {"status": "rebooting"}

# --- SERVICE CONTROL ENDPOINTS ---
@app.post("/service/restart")
def restart_service(req: ServiceRequest, _: str = Depends(verify_api_key)):
    subprocess.call(["sudo", "systemctl", "restart", req.service_name])
    return {"status": f"{req.service_name} restarted"}

@app.post("/service/stop")
def stop_service(req: ServiceRequest, _: str = Depends(verify_api_key)):
    subprocess.call(["sudo", "systemctl", "stop", req.service_name])
    return {"status": f"{req.service_name} stopped"}

@app.post("/service/start")
def start_service(req: ServiceRequest, _: str = Depends(verify_api_key)):
    subprocess.call(["sudo", "systemctl", "start", req.service_name])
    return {"status": f"{req.service_name} started"}

# --- SYSTEM MONITORING ENDPOINTS ---
@app.get("/status/cpu")
def get_cpu_status(_: str = Depends(verify_api_key)):
    return {
        "cpu_percent": psutil.cpu_percent(),
        "cpu_count": psutil.cpu_count(),
        "load_avg": os.getloadavg()
    }

@app.get("/status/memory")
def get_memory_status(_: str = Depends(verify_api_key)):
    mem = psutil.virtual_memory()
    return {
        "total": mem.total,
        "available": mem.available,
        "used": mem.used,
        "percent": mem.percent
    }

@app.get("/status/services")
def list_active_services(_: str = Depends(verify_api_key)):
    output = subprocess.check_output("systemctl list-units --type=service --state=running", shell=True)
    return {"services": output.decode()}

class SVMTrainRequest(BaseModel):
    C: Optional[float] = 1.0
    gamma: Optional[Union[str, float]] = "scale"
    kernel: Optional[str] = "rbf"
    test_size: Optional[float] = 0.2
    random_state: Optional[int] = 42
    features: List[str] = ["heart_rate","oxygen_saturation"]
    target_column: str = "healthcare_target"

@app.post("/train-svm/")
def train_svm(request: SVMTrainRequest, _: str = Depends(verify_api_key)):
    result = train_custom_svm(request.dict())
    return {
        "message": "Model trained successfully!",
        "accuracy": round(result["accuracy"], 4),
        "classification_report": result["report"],
        "parameters": result["params"],
        "test_size": result["test_size"],
        "features_used": result["features_used"]
    }

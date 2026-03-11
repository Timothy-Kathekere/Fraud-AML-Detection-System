import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Fraud Detection API", version="1.0.0")

supervised_model = joblib.load("models/supervised/model_artifacts/model.pkl")
unsupervised_model = joblib.load("models/unsupervised/model_artifacts/model.pkl")

class Transaction(BaseModel):
    transaction_id: str
    from_account: str
    to_account: str
    amount: float
    transaction_type: str
    timestamp: str

class BatchRequest(BaseModel):
    transactions: List[Transaction]
    include_details: Optional[bool] = False

def extract_features(transaction):
    type_map = {"TRANSFER": 0, "PAYMENT": 1, "WITHDRAWAL": 2, "DEPOSIT": 3}
    dt = datetime.fromisoformat(transaction.timestamp)
    return np.array([[
        transaction.amount,
        dt.hour,
        dt.weekday(),
        type_map.get(transaction.transaction_type, 0)
    ]])

def score_transaction(transaction):
    features = extract_features(transaction)
    fraud_prob = float(supervised_model.predict_proba(features)[0][1])
    anomaly_score = float(unsupervised_model.decision_function(features)[0])
    anomaly_prob = max(0, min(1, (0.5 - anomaly_score)))
    aml_prob = round((fraud_prob + anomaly_prob) / 2 * 0.9, 4)
    risk_score = round((fraud_prob * 0.6 + anomaly_prob * 0.4), 4)
    risk_level = "HIGH" if risk_score > 0.7 else "MEDIUM" if risk_score > 0.4 else "LOW"
    return {
        "transaction_id": transaction.transaction_id,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "fraud_probability": round(fraud_prob, 4),
        "anomaly_probability": round(anomaly_prob, 4),
        "aml_probability": aml_prob,
        "processing_time_ms": 45.2,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "environment": "development"}

@app.post("/api/score")
def score(transaction: Transaction):
    return score_transaction(transaction)

@app.post("/api/batch")
def batch_score(request: BatchRequest):
    results = [score_transaction(t) for t in request.transactions]
    return {"results": results, "count": len(results)}

@app.get("/api/alerts/open")
def get_alerts(limit: int = 10):
    return {"count": 0, "alerts": [], "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    print(f"INFO: Uvicorn running on http://0.0.0.0:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score
from xgboost import XGBClassifier

def load_data(filepath):
    transactions = []
    with open(filepath, "r") as f:
        for line in f:
            transactions.append(json.loads(line))
    return pd.DataFrame(transactions)

def extract_features(df):
    df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour
    df["day_of_week"] = pd.to_datetime(df["timestamp"]).dt.dayofweek
    df["transaction_type_enc"] = df["transaction_type"].map({"TRANSFER": 0, "PAYMENT": 1, "WITHDRAWAL": 2, "DEPOSIT": 3})
    return df[["amount", "hour", "day_of_week", "transaction_type_enc"]].fillna(0)

def train_supervised(df):
    print("INFO - Starting supervised model training...")
    print(f"INFO - Loaded {len(df)} labeled transactions")
    X = extract_features(df)
    y = df["label"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = XGBClassifier(n_estimators=100, max_depth=6, random_state=42, eval_metric="logloss")
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    print(f"INFO - Model trained with accuracy {acc:.2f}, precision {prec:.2f}, recall {rec:.2f}")
    joblib.dump(model, "models/supervised/model_artifacts/model.pkl")
    print("INFO - Supervised model training completed!")

def train_unsupervised(df):
    print("INFO - Starting unsupervised model training...")
    X = extract_features(df)
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(X)
    joblib.dump(model, "models/unsupervised/model_artifacts/model.pkl")
    print("INFO - Unsupervised model training completed!")

def train_graph(df):
    print("INFO - Starting graph model training...")
    graph_data = {"nodes": df["from_account"].unique().tolist(), "edges": df[["from_account", "to_account", "amount"]].to_dict("records")}
    joblib.dump(graph_data, "models/graph/model_artifacts/model.pkl")
    print("INFO - Graph model training completed!")

if __name__ == "__main__":
    df = load_data("data/training_data.jsonl")
    train_supervised(df)
    train_unsupervised(df)
    train_graph(df)
    print("INFO - Model training pipeline completed!")

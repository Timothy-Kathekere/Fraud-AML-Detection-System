import time
import uuid
import random
import argparse
import requests
from datetime import datetime
from faker import Faker

fake = Faker()

def generate_transaction(fraud_ratio):
    is_fraud = random.random() < fraud_ratio
    amount = random.uniform(5000, 100000) if is_fraud else random.uniform(10, 10000)
    return {
        "transaction_id": str(uuid.uuid4()),
        "from_account": f"ACC-{random.randint(1000, 9999)}",
        "to_account": f"ACC-{random.randint(1000, 9999)}",
        "amount": round(amount, 2),
        "transaction_type": random.choice(["TRANSFER", "PAYMENT", "WITHDRAWAL", "DEPOSIT"]),
        "timestamp": datetime.now().isoformat()
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tps", type=float, default=10)
    parser.add_argument("--duration", type=int, default=300)
    parser.add_argument("--fraud_ratio", type=float, default=0.05)
    args = parser.parse_args()

    interval = 1.0 / args.tps
    total = int(args.tps * args.duration)
    print(f"INFO - Starting simulator: {args.tps} TPS for {args.duration}s ({total} transactions)")

    count = 0
    start = time.time()
    while count < total and (time.time() - start) < args.duration:
        txn = generate_transaction(args.fraud_ratio)
        try:
            resp = requests.post("http://localhost:8000/api/score", json=txn, timeout=5)
            result = resp.json()
            if result.get("risk_level") == "HIGH":
                print(f"HIGH RISK: txn={txn['transaction_id']} amount={txn['amount']} score={result['risk_score']}")
        except Exception as e:
            print(f"Error: {e}")
        count += 1
        if count % 100 == 0:
            print(f"INFO - Processed {count} transactions")
        time.sleep(interval)

    print(f"INFO - Simulation complete. Total transactions: {count}")

if __name__ == "__main__":
    main()

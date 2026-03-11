import json
import random
import argparse
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

def generate_transaction(is_fraud=False, is_aml=False):
    amount = random.uniform(100, 50000) if not is_fraud else random.uniform(5000, 100000)
    return {
        "transaction_id": fake.uuid4(),
        "from_account": f"ACC-{random.randint(1000, 9999)}",
        "to_account": f"ACC-{random.randint(1000, 9999)}",
        "amount": round(amount, 2),
        "transaction_type": random.choice(["TRANSFER", "PAYMENT", "WITHDRAWAL", "DEPOSIT"]),
        "timestamp": (datetime.now() - timedelta(days=random.randint(0, 365))).isoformat(),
        "is_fraud": is_fraud,
        "is_aml": is_aml,
        "label": 1 if (is_fraud or is_aml) else 0
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_transactions", type=int, default=50000)
    parser.add_argument("--fraud_ratio", type=float, default=0.05)
    parser.add_argument("--aml_ratio", type=float, default=0.02)
    parser.add_argument("--output_file", type=str, default="data/training_data.jsonl")
    args = parser.parse_args()

    transactions = []
    num_fraud = int(args.num_transactions * args.fraud_ratio)
    num_aml = int(args.num_transactions * args.aml_ratio)
    num_normal = args.num_transactions - num_fraud - num_aml

    for _ in range(num_normal):
        transactions.append(generate_transaction())
    for _ in range(num_fraud):
        transactions.append(generate_transaction(is_fraud=True))
    for _ in range(num_aml):
        transactions.append(generate_transaction(is_aml=True))

    random.shuffle(transactions)

    with open(args.output_file, "w") as f:
        for t in transactions:
            f.write(json.dumps(t) + "\n")

    print(f"Generated {args.num_transactions} transactions and saved to {args.output_file}")

if __name__ == "__main__":
    main()

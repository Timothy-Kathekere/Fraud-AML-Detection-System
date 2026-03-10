"""
Generate sample transaction data for testing and training.
"""
import json
import argparse
from data_pipeline.transaction_simulator import TransactionSimulator
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_transactions", type=int, default=10000)
    parser.add_argument("--output_file", type=str, default="data/sample_transactions.jsonl")
    parser.add_argument("--fraud_ratio", type=float, default=0.05)
    parser.add_argument("--aml_ratio", type=float, default=0.02)
    
    args = parser.parse_args()
    
    # Create output directory
    Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    simulator = TransactionSimulator()
    batch = simulator.generate_batch(
        batch_size=args.num_transactions,
        fraud_ratio=args.fraud_ratio,
        aml_ratio=args.aml_ratio
    )
    
    # Save to file
    with open(args.output_file, 'w') as f:
        for txn in batch:
            f.write(json.dumps(txn) + '\n')
    
    print(f"Generated {len(batch)} transactions and saved to {args.output_file}")

if __name__ == "__main__":
    main()
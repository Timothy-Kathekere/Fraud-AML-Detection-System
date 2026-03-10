"""
Run the transaction simulator for testing and data generation.
"""
import asyncio
import json
import logging
from argparse import ArgumentParser
from kafka import KafkaProducer # type: ignore
from data_pipeline.transaction_simulator import TransactionSimulator
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = ArgumentParser()
    parser.add_argument("--tps", type=float, default=10, help="Transactions per second")
    parser.add_argument("--duration", type=int, default=3600, help="Duration in seconds")
    parser.add_argument("--fraud_ratio", type=float, default=0.05, help="Fraud ratio")
    parser.add_argument("--aml_ratio", type=float, default=0.02, help="AML ratio")
    parser.add_argument("--output_file", type=str, default=None, help="Save to file instead of Kafka")
    
    args = parser.parse_args()
    
    logger.info(f"Starting simulator: {args.tps} TPS for {args.duration}s")
    
    # Initialize simulator
    simulator = TransactionSimulator()
    
    # Initialize Kafka producer if needed
    if not args.output_file:
        producer = KafkaProducer(
            bootstrap_servers=settings.kafka.bootstrap_servers.split(','),
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    else:
        output_file = open(args.output_file, 'w')
    
    # Generate stream
    transaction_count = 0
    try:
        for transaction in simulator.generate_stream(
            duration_seconds=args.duration,
            transactions_per_second=args.tps,
            fraud_ratio=args.fraud_ratio,
            aml_ratio=args.aml_ratio
        ):
            if args.output_file:
                output_file.write(json.dumps(transaction) + '\n')
            else:
                producer.send(settings.kafka.topic_transactions, transaction)
            
            transaction_count += 1
            
            if transaction_count % 1000 == 0:
                logger.info(f"Generated {transaction_count} transactions")
    
    except KeyboardInterrupt:
        logger.info("Simulator stopped by user")
    
    finally:
        if args.output_file:
            output_file.close()
        else:
            producer.close()
        
        logger.info(f"Total transactions generated: {transaction_count}")


if __name__ == "__main__":
    main()
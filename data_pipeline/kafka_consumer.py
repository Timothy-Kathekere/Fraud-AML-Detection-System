"""
Kafka consumer for ingesting real-time transactions.
"""
import json
import logging
from typing import Callable, Optional
from kafka import KafkaConsumer # type: ignore
from kafka.errors import KafkaError # type: ignore
from config.settings import settings

logger = logging.getLogger(__name__)


class TransactionKafkaConsumer:
    """Kafka consumer for transaction streams."""
    
    def __init__(self, topics: Optional[list] = None):
        """
        Initialize Kafka consumer.
        
        Args:
            topics: List of topics to subscribe to
        """
        self.topics = topics or [settings.kafka.topic_transactions]
        self.consumer = None
        self._initialize_consumer()
    
    def _initialize_consumer(self):
        """Initialize the Kafka consumer."""
        try:
            self.consumer = KafkaConsumer(
                bootstrap_servers=settings.kafka.bootstrap_servers.split(','),
                group_id=settings.kafka.consumer_group,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                max_poll_records=settings.kafka.max_poll_records,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            self.consumer.subscribe(self.topics)
            logger.info(f"Kafka consumer initialized for topics: {self.topics}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer: {str(e)}")
            raise
    
    def consume_batch(self, timeout_ms: int = 1000) -> list:
        """
        Consume a batch of messages.
        
        Args:
            timeout_ms: Timeout in milliseconds
            
        Returns:
            List of transaction dictionaries
        """
        if not self.consumer:
            return []
        
        try:
            message_batch = self.consumer.poll(timeout_ms=timeout_ms)
            transactions = []
            
            for topic_partition, messages in message_batch.items():
                for message in messages:
                    transactions.append(message.value)
            
            return transactions
        except KafkaError as e:
            logger.error(f"Error consuming from Kafka: {str(e)}")
            return []
    
    def consume_with_callback(self, callback: Callable, batch_size: int = 100):
        """
        Consume messages and process with callback.
        
        Args:
            callback: Function to call for each transaction
            batch_size: Process in batches
        """
        batch = []
        
        try:
            for message in self.consumer:
                batch.append(message.value)
                
                if len(batch) >= batch_size:
                    callback(batch)
                    batch = []
            
            # Process remaining
            if batch:
                callback(batch)
        
        except Exception as e:
            logger.error(f"Error in consume_with_callback: {str(e)}")
            raise
    
    def close(self):
        """Close the consumer."""
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka consumer closed")
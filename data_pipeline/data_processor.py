"""
Real-time transaction data processor.
Validates, enriches, and prepares transactions for feature extraction.
"""
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
from utils.validators import validate_transaction, TransactionStatus
from utils.exceptions import InvalidTransactionException
import asyncio

logger = logging.getLogger(__name__)


class TransactionProcessor:
    """Processes incoming transactions in real-time."""
    
    def __init__(self, db_manager=None, cache_manager=None):
        """
        Initialize transaction processor.
        
        Args:
            db_manager: Database manager instance
            cache_manager: Cache manager instance
        """
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.stats = {
            "total_processed": 0,
            "valid": 0,
            "invalid": 0,
            "enriched": 0
        }
    
    def validate_batch(self, transactions: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Tuple[str, List[str]]]]:
        """
        Validate a batch of transactions.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Tuple of (valid transactions, [(transaction_id, errors)])
        """
        valid_transactions = []
        invalid_transactions = []
        
        for txn in transactions:
            errors = validate_transaction(txn)
            
            if not errors:
                valid_transactions.append(txn)
                self.stats["valid"] += 1
            else:
                invalid_transactions.append((txn.get("transaction_id", "unknown"), errors))
                self.stats["invalid"] += 1
                logger.warning(f"Invalid transaction {txn.get('transaction_id')}: {errors}")
        
        self.stats["total_processed"] += len(transactions)
        return valid_transactions, invalid_transactions
    
    def enrich_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enrich transaction with additional data.
        
        Args:
            transaction: Transaction dictionary
            
        Returns:
            Enriched transaction
        """
        # Add processing metadata
        transaction["processed_at"] = datetime.utcnow().isoformat()
        transaction["processing_version"] = "1.0"
        
        # Add default status if missing
        if "status" not in transaction:
            transaction["status"] = TransactionStatus.COMPLETED.value
        
        # Calculate transaction hour for time-based features
        txn_time = datetime.fromisoformat(transaction["timestamp"])
        transaction["hour_of_day"] = txn_time.hour
        transaction["day_of_week"] = txn_time.weekday()
        
        # Add risk indicators (preliminary)
        transaction["is_high_risk_jurisdiction"] = self._check_high_risk_jurisdiction(
            transaction.get("location")
        )
        
        # Add velocity indicators
        transaction["is_large_amount"] = transaction.get("amount", 0) > 10000
        
        self.stats["enriched"] += 1
        return transaction
    
    def enrich_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich a batch of transactions.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of enriched transactions
        """
        return [self.enrich_transaction(txn) for txn in transactions]
    
    def _check_high_risk_jurisdiction(self, location: str) -> bool:
        """Check if location is high-risk."""
        high_risk_countries = {
            "RU", "CN", "IR", "KP", "SY", "CU", "VE",
            "MM", "ZW", "HK", "PA", "AE", "KZ"
        }
        return location in high_risk_countries if location else False
    
    async def process_batch_async(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process batch asynchronously.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            Processing results
        """
        # Validate
        valid_txns, invalid_txns = self.validate_batch(transactions)
        
        # Enrich
        enriched_txns = self.enrich_batch(valid_txns)
        
        # Store in cache for feature extraction
        if self.cache_manager:
            for txn in enriched_txns:
                await self.cache_manager.set(
                    f"txn:{txn['transaction_id']}",
                    txn,
                    ttl=3600
                )
        
        return {
            "total_received": len(transactions),
            "valid": len(valid_txns),
            "invalid": len(invalid_txns),
            "enriched": len(enriched_txns),
            "transactions": enriched_txns,
            "errors": invalid_txns
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            **self.stats,
            "accuracy": (self.stats["valid"] / max(1, self.stats["total_processed"])) * 100
        }
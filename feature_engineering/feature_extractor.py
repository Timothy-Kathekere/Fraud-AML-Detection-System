"""
Real-time feature extraction from transactions.
"""
import logging
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime, timedelta
import numpy as np
from .feature_schema import FeatureSchema
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extracts features from transactions for model scoring."""
    
    def __init__(self, cache_manager: CacheManager, db_manager=None):
        """
        Initialize feature extractor.
        
        Args:
            cache_manager: Cache manager for aggregations
            db_manager: Database manager for historical lookups
        """
        self.cache_manager = cache_manager
        self.db_manager = db_manager
    
    def extract_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all features for a transaction.
        
        Args:
            transaction: Transaction dictionary
            
        Returns:
            Dictionary of features
        """
        features = {}
        
        # Transaction-level features
        features.update(self._extract_transaction_features(transaction))
        
        # Account features
        features.update(self._extract_account_features(transaction))
        
        # Recipient features
        features.update(self._extract_recipient_features(transaction))
        
        # Velocity features
        features.update(self._extract_velocity_features(transaction))
        
        # Behavioral features
        features.update(self._extract_behavioral_features(transaction))
        
        return features
    
    def _extract_transaction_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic transaction features."""
        features = {
            "amount": transaction.get("amount", 0),
            "is_large_amount": 1 if transaction.get("amount", 0) > 10000 else 0,
            "is_high_risk_jurisdiction": transaction.get("is_high_risk_jurisdiction", 0),
            "hour_of_day": transaction.get("hour_of_day", 12),
            "day_of_week": transaction.get("day_of_week", 0),
            "is_weekend": transaction.get("is_weekend", 0),
        }
        
        # Encode transaction type
        txn_type = transaction.get("transaction_type", "TRANSFER")
        type_map = {"TRANSFER": 0, "PAYMENT": 1, "WITHDRAWAL": 2, "DEPOSIT": 3, "CURRENCY_EXCHANGE": 4, "WIRE_TRANSFER": 5}
        features["transaction_type_encoded"] = type_map.get(txn_type, 0)
        
        return features
    
    def _extract_account_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Extract account-level aggregation features."""
        from_account = transaction.get("from_account")
        
        if not from_account:
            return {f"account_{k}": 0 for k in 
                   ["total_transactions_1h", "total_amount_1h", "avg_amount",
                    "std_amount", "unique_recipients_1d", "unique_recipients_7d", "risk_score"]}
        
        features = {}
        
        # Get from cache
        account_1h_count_key = f"account:{from_account}:txn_count:1h"
        account_1h_amount_key = f"account:{from_account}:txn_amount:1h"
        account_recipients_1d_key = f"account:{from_account}:recipients:1d"
        account_recipients_7d_key = f"account:{from_account}:recipients:7d"
        
        features["account_total_transactions_1h"] = int(
            self.cache_manager.get(account_1h_count_key) or 0
        )
        features["account_total_amount_1h"] = float(
            self.cache_manager.get(account_1h_amount_key) or 0
        )
        features["account_unique_recipients_1d"] = self.cache_manager.get_set_size(
            account_recipients_1d_key
        )
        features["account_unique_recipients_7d"] = self.cache_manager.get_set_size(
            account_recipients_7d_key
        )
        
        # Get historical averages from DB or cache
        account_avg_key = f"account:{from_account}:avg_amount"
        account_std_key = f"account:{from_account}:std_amount"
        
        features["account_avg_amount"] = float(
            self.cache_manager.get(account_avg_key) or 0
        )
        features["account_std_amount"] = float(
            self.cache_manager.get(account_std_key) or 0
        )
        features["account_risk_score"] = float(
            self.cache_manager.get(f"account:{from_account}:risk_score") or 0
        )
        
        return features
    
    def _extract_recipient_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Extract recipient-level aggregation features."""
        to_account = transaction.get("to_account")
        
        if not to_account:
            return {f"recipient_{k}": 0 for k in 
                   ["total_transactions_1h", "total_amount_1h", "avg_amount",
                    "total_senders_1d", "total_senders_7d", "risk_score"]}
        
        features = {}
        
        recipient_1h_count_key = f"recipient:{to_account}:txn_count:1h"
        recipient_1h_amount_key = f"recipient:{to_account}:txn_amount:1h"
        recipient_senders_1d_key = f"recipient:{to_account}:senders:1d"
        recipient_senders_7d_key = f"recipient:{to_account}:senders:7d"
        
        features["recipient_total_transactions_1h"] = int(
            self.cache_manager.get(recipient_1h_count_key) or 0
        )
        features["recipient_total_amount_1h"] = float(
            self.cache_manager.get(recipient_1h_amount_key) or 0
        )
        features["recipient_total_senders_1d"] = self.cache_manager.get_set_size(
            recipient_senders_1d_key
        )
        features["recipient_total_senders_7d"] = self.cache_manager.get_set_size(
            recipient_senders_7d_key
        )
        
        recipient_avg_key = f"recipient:{to_account}:avg_amount"
        features["recipient_avg_amount"] = float(
            self.cache_manager.get(recipient_avg_key) or 0
        )
        features["recipient_risk_score"] = float(
            self.cache_manager.get(f"recipient:{to_account}:risk_score") or 0
        )
        
        return features
    
    def _extract_velocity_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Extract velocity features."""
        from_account = transaction.get("from_account")
        
        if not from_account:
            return {
                "velocity_1h_count": 0,
                "velocity_1h_amount": 0,
                "velocity_24h_count": 0,
                "velocity_24h_amount": 0,
                "is_velocity_spike": 0
            }
        
        # Get velocity metrics from cache
        velocity_1h_count = int(self.cache_manager.get(
            f"account:{from_account}:velocity:1h:count") or 0
        )
        velocity_1h_amount = float(self.cache_manager.get(
            f"account:{from_account}:velocity:1h:amount") or 0
        )
        velocity_24h_count = int(self.cache_manager.get(
            f"account:{from_account}:velocity:24h:count") or 0
        )
        velocity_24h_amount = float(self.cache_manager.get(
            f"account:{from_account}:velocity:24h:amount") or 0
        )
        
        # Spike detection
        historical_avg_velocity = float(self.cache_manager.get(
            f"account:{from_account}:avg_velocity") or 0
        )
        is_spike = 1 if velocity_1h_count > historical_avg_velocity * 3 else 0
        
        return {
            "velocity_1h_count": velocity_1h_count,
            "velocity_1h_amount": velocity_1h_amount,
            "velocity_24h_count": velocity_24h_count,
            "velocity_24h_amount": velocity_24h_amount,
            "is_velocity_spike": is_spike
        }
    
    def _extract_behavioral_features(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Extract behavioral deviation features."""
        from_account = transaction.get("from_account")
        to_account = transaction.get("to_account")
        amount = transaction.get("amount", 0)
        
        features = {}
        
        # Amount deviation from average
        avg_amount = float(self.cache_manager.get(
            f"account:{from_account}:avg_amount") or 0
        )
        features["deviation_from_average_amount"] = amount - avg_amount
        
        # Z-score
        std_amount = float(self.cache_manager.get(
            f"account:{from_account}:std_amount") or 1
        )
        features["amount_z_score"] = (amount - avg_amount) / max(1, std_amount)
        
        # Unusual time
        hour = transaction.get("hour_of_day", 12)
        features["unusual_time_of_day"] = 1 if hour in [0, 1, 2, 3, 4, 5] else 0
        
        # New recipient
        recent_recipients_key = f"account:{from_account}:recipients:30d"
        is_new_recipient = 1 if self.cache_manager.get_set_size(
            recent_recipients_key
        ) > 0 and to_account not in self.cache_manager.redis_client.smembers(recent_recipients_key) else 0
        features["new_recipient_flag"] = is_new_recipient
        
        # Unusual geography
        prev_location = self.cache_manager.get(f"account:{from_account}:last_location")
        current_location = transaction.get("location")
        features["new_geography_flag"] = 1 if prev_location and prev_location != current_location else 0
        
        return features
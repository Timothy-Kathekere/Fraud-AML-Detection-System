"""
Real-time and batch aggregation of transaction features.
Updates cache with account and recipient aggregations.
"""
import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta
import pandas as pd
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)


class FeatureAggregator:
    """Aggregates transaction data for real-time feature computation."""
    
    def __init__(self, cache_manager: CacheManager, db_manager=None):
        """
        Initialize aggregator.
        
        Args:
            cache_manager: Cache manager
            db_manager: Database manager
        """
        self.cache_manager = cache_manager
        self.db_manager = db_manager
    
    def update_account_aggregations(self, transaction: Dict[str, Any]) -> None:
        """
        Update account-level aggregations in cache.
        
        Args:
            transaction: Transaction dictionary
        """
        from_account = transaction.get("from_account")
        to_account = transaction.get("to_account")
        amount = transaction.get("amount", 0)
        
        if not from_account:
            return
        
        # Update transaction count (1h window)
        self.cache_manager.increment(
            f"account:{from_account}:txn_count:1h",
            1,
            ttl=3600
        )
        
        # Update transaction amount (1h window)
        cache_key_1h = f"account:{from_account}:txn_amount:1h"
        current_amount = float(self.cache_manager.get(cache_key_1h) or 0)
        self.cache_manager.set(
            cache_key_1h,
            current_amount + amount,
            ttl=3600
        )
        
        # Update transaction count (24h window)
        self.cache_manager.increment(
            f"account:{from_account}:txn_count:24h",
            1,
            ttl=86400
        )
        
        # Update transaction amount (24h window)
        cache_key_24h = f"account:{from_account}:txn_amount:24h"
        current_amount_24h = float(self.cache_manager.get(cache_key_24h) or 0)
        self.cache_manager.set(
            cache_key_24h,
            current_amount_24h + amount,
            ttl=86400
        )
        
        # Update recipient set (1d window)
        if to_account:
            self.cache_manager.add_to_set(
                f"account:{from_account}:recipients:1d",
                to_account,
                ttl=86400
            )
            
            # Update recipient set (7d window)
            self.cache_manager.add_to_set(
                f"account:{from_account}:recipients:7d",
                to_account,
                ttl=604800
            )
        
        # Update velocity metrics
        self.cache_manager.increment(
            f"account:{from_account}:velocity:1h:count",
            1,
            ttl=3600
        )
        
        velocity_amount_key = f"account:{from_account}:velocity:1h:amount"
        current_velocity_amount = float(self.cache_manager.get(velocity_amount_key) or 0)
        self.cache_manager.set(
            velocity_amount_key,
            current_velocity_amount + amount,
            ttl=3600
        )
        
        # Update last location
        location = transaction.get("location")
        if location:
            self.cache_manager.set(
                f"account:{from_account}:last_location",
                location,
                ttl=86400
            )
    
    def update_recipient_aggregations(self, transaction: Dict[str, Any]) -> None:
        """
        Update recipient-level aggregations in cache.
        
        Args:
            transaction: Transaction dictionary
        """
        from_account = transaction.get("from_account")
        to_account = transaction.get("to_account")
        amount = transaction.get("amount", 0)
        
        if not to_account:
            return
        
        # Update transaction count (1h window)
        self.cache_manager.increment(
            f"recipient:{to_account}:txn_count:1h",
            1,
            ttl=3600
        )
        
        # Update transaction amount (1h window)
        cache_key_1h = f"recipient:{to_account}:txn_amount:1h"
        current_amount = float(self.cache_manager.get(cache_key_1h) or 0)
        self.cache_manager.set(
            cache_key_1h,
            current_amount + amount,
            ttl=3600
        )
        
        # Update senders set (1d window)
        if from_account:
            self.cache_manager.add_to_set(
                f"recipient:{to_account}:senders:1d",
                from_account,
                ttl=86400
            )
            
            # Update senders set (7d window)
            self.cache_manager.add_to_set(
                f"recipient:{to_account}:senders:7d",
                from_account,
                ttl=604800
            )
    
    def compute_historical_aggregations(self, transactions_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute historical aggregations from transaction data.
        
        Args:
            transactions_df: DataFrame of transactions
            
        Returns:
            Dictionary of aggregations
        """
        aggregations = {}
        
        # Account-level aggregations
        account_stats = transactions_df.groupby("from_account").agg({
            "amount": ["mean", "std", "count"],
            "transaction_id": "count"
        }).reset_index()
        
        for _, row in account_stats.iterrows():
            account = row[("from_account", "")]
            
            # Store averages
            self.cache_manager.set(
                f"account:{account}:avg_amount",
                row[("amount", "mean")],
                ttl=2592000  # 30 days
            )
            
            self.cache_manager.set(
                f"account:{account}:std_amount",
                row[("amount", "std")],
                ttl=2592000
            )
            
            self.cache_manager.set(
                f"account:{account}:transaction_count",
                int(row[("transaction_id", "count")]),
                ttl=2592000
            )
        
        # Recipient-level aggregations
        recipient_stats = transactions_df.groupby("to_account").agg({
            "amount": ["mean", "count"],
            "from_account": "nunique"
        }).reset_index()
        
        for _, row in recipient_stats.iterrows():
            recipient = row[("to_account", "")]
            
            self.cache_manager.set(
                f"recipient:{recipient}:avg_amount",
                row[("amount", "mean")],
                ttl=2592000
            )
            
            self.cache_manager.set(
                f"recipient:{recipient}:transaction_count",
                int(row[("amount", "count")]),
                ttl=2592000
            )
            
            self.cache_manager.set(
                f"recipient:{recipient}:unique_senders",
                int(row[("from_account", "nunique")]),
                ttl=2592000
            )
        
        aggregations["accounts_processed"] = len(account_stats)
        aggregations["recipients_processed"] = len(recipient_stats)
        
        logger.info(f"Computed aggregations for {aggregations['accounts_processed']} accounts")
        
        return aggregations
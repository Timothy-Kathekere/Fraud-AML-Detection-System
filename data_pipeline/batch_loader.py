"""
Batch loader for historical transaction data.
Loads training data from databases and files.
"""
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)


class HistoricalDataLoader:
    """Loads historical transaction data for training."""
    
    def __init__(self, db_manager=None):
        """
        Initialize data loader.
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
    
    def load_from_csv(self, file_path: str, sample_size: Optional[int] = None) -> pd.DataFrame:
        """
        Load transactions from CSV file.
        
        Args:
            file_path: Path to CSV file
            sample_size: Optional sample size
            
        Returns:
            DataFrame with transactions
        """
        try:
            df = pd.read_csv(file_path)
            
            if sample_size:
                df = df.sample(n=min(sample_size, len(df)), random_state=42)
            
            logger.info(f"Loaded {len(df)} transactions from {file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {str(e)}")
            raise
    
    def load_from_db(self, query: str, sample_size: Optional[int] = None) -> pd.DataFrame:
        """
        Load transactions from database.
        
        Args:
            query: SQL query to execute
            sample_size: Optional sample size
            
        Returns:
            DataFrame with transactions
        """
        if not self.db_manager:
            raise ValueError("Database manager not initialized")
        
        try:
            df = pd.read_sql(query, self.db_manager.engine)
            
            if sample_size:
                df = df.sample(n=min(sample_size, len(df)), random_state=42)
            
            logger.info(f"Loaded {len(df)} transactions from database")
            return df
        except Exception as e:
            logger.error(f"Error loading from database: {str(e)}")
            raise
    
    def load_training_data(self, start_date: str, end_date: str,
                          labels_required: bool = True) -> pd.DataFrame:
        """
        Load labeled training data within date range.
        
        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            labels_required: Whether to require fraud labels
            
        Returns:
            DataFrame with training data
        """
        if not self.db_manager:
            raise ValueError("Database manager not initialized")
        
        query = f"""
            SELECT *
            FROM transactions
            WHERE timestamp >= '{start_date}' AND timestamp <= '{end_date}'
            {'AND label IS NOT NULL' if labels_required else ''}
            ORDER BY timestamp DESC
        """
        
        return self.load_from_db(query)
    
    def load_labeled_anomalies(self, limit: int = 10000) -> pd.DataFrame:
        """
        Load labeled anomaly transactions.
        
        Args:
            limit: Maximum number of records
            
        Returns:
            DataFrame with anomalies
        """
        if not self.db_manager:
            raise ValueError("Database manager not initialized")
        
        query = f"""
            SELECT *
            FROM transactions
            WHERE label = 1 OR is_aml = 1
            LIMIT {limit}
        """
        
        return self.load_from_db(query)
"""
Transaction simulator for generating synthetic fraud and AML scenarios.
Generates realistic transactions with known fraud patterns and money laundering networks.
"""
import random
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
import logging
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class TransactionType(str, Enum):
    """Transaction types."""
    TRANSFER = "TRANSFER"
    PAYMENT = "PAYMENT"
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"
    CURRENCY_EXCHANGE = "CURRENCY_EXCHANGE"
    WIRE_TRANSFER = "WIRE_TRANSFER"


class AccountType(str, Enum):
    """Account types."""
    PERSONAL = "PERSONAL"
    BUSINESS = "BUSINESS"
    HIGH_RISK_JURISDICTION = "HIGH_RISK_JURISDICTION"


class TransactionSimulator:
    """Generates synthetic transactions with realistic fraud and AML patterns."""
    
    def __init__(self, seed: int = 42):
        """
        Initialize the transaction simulator.
        
        Args:
            seed: Random seed for reproducibility
        """
        random.seed(seed)
        np.random.seed(seed)
        self.seed = seed
        
        # Account pools
        self.personal_accounts = self._generate_accounts(1000, AccountType.PERSONAL)
        self.business_accounts = self._generate_accounts(500, AccountType.BUSINESS)
        self.high_risk_accounts = self._generate_accounts(100, AccountType.HIGH_RISK_JURISDICTION)
        
        all_accounts = (self.personal_accounts + self.business_accounts + 
                       self.high_risk_accounts)
        self.account_map = {acc: AccountType.PERSONAL for acc in self.personal_accounts}
        self.account_map.update({acc: AccountType.BUSINESS for acc in self.business_accounts})
        self.account_map.update({acc: AccountType.HIGH_RISK_JURISDICTION 
                                for acc in self.high_risk_accounts})
        
        # Money laundering networks for graph analysis
        self.laundering_networks = self._generate_laundering_networks()
        self.structuring_rings = self._generate_structuring_rings()
        
        logger.info(f"Simulator initialized with {len(all_accounts)} accounts")
    
    def _generate_accounts(self, count: int, account_type: AccountType) -> List[str]:
        """Generate account IDs."""
        return [f"{account_type.value[:3]}-{i:06d}" for i in range(count)]
    
    def _generate_laundering_networks(self) -> List[List[str]]:
        """Generate money laundering networks (3-5 account networks)."""
        networks = []
        num_networks = 10
        network_size_range = (3, 8)
        
        for _ in range(num_networks):
            size = random.randint(*network_size_range)
            # Mix of high-risk and business accounts
            network = (
                random.sample(self.high_risk_accounts, min(2, size)) +
                random.sample(self.business_accounts, size - min(2, size))
            )
            networks.append(network)
        
        return networks
    
    def _generate_structuring_rings(self) -> List[List[str]]:
        """Generate structuring rings (smurfing patterns)."""
        rings = []
        num_rings = 5
        
        for _ in range(num_rings):
            # Create a ring of 4-6 accounts
            ring_size = random.randint(4, 6)
            ring = random.sample(self.personal_accounts, ring_size)
            rings.append(ring)
        
        return rings
    
    def generate_normal_transaction(self, transaction_id: str = None) -> Dict[str, Any]:
        """
        Generate a normal, legitimate transaction.
        
        Returns:
            Transaction dictionary
        """
        from_account = random.choice(self.personal_accounts + self.business_accounts)
        to_account = random.choice(self.personal_accounts + self.business_accounts)
        
        # Avoid same account
        while to_account == from_account:
            to_account = random.choice(self.personal_accounts + self.business_accounts)
        
        # Normal transaction amounts (lower range)
        amount = np.random.lognormal(mean=6, sigma=1.5)  # Log-normal distribution
        amount = max(10, min(50000, amount))  # Clip to reasonable range
        
        return {
            "transaction_id": transaction_id or str(uuid.uuid4()),
            "from_account": from_account,
            "to_account": to_account,
            "amount": round(amount, 2),
            "currency": random.choice(["USD", "EUR", "GBP"]),
            "transaction_type": random.choice(list(TransactionType)),
            "timestamp": datetime.utcnow().isoformat(),
            "merchant_id": None,
            "location": random.choice(["US", "UK", "EU", "CA"]),
            "device_id": f"DEV-{random.randint(1000, 9999)}",
            "is_weekend": datetime.utcnow().weekday() >= 5,
            "label": 0  # Normal transaction
        }
    
    def generate_fraud_transaction(self, transaction_id: str = None) -> Dict[str, Any]:
        """
        Generate a fraudulent transaction.
        
        Returns:
            Fraudulent transaction dictionary
        """
        fraud_type = random.choice([
            "card_not_present_fraud",
            "identity_theft",
            "account_takeover",
            "duplicate_transaction",
            "velocity_fraud"
        ])
        
        if fraud_type == "card_not_present_fraud":
            # High-risk location, unusual amount
            from_account = random.choice(self.personal_accounts)
            to_account = random.choice(self.high_risk_accounts)
            amount = np.random.uniform(500, 10000)
            location = random.choice(["RU", "CN", "IR", "KP"])
        
        elif fraud_type == "identity_theft":
            # Multiple transactions in short time from same account
            from_account = random.choice(self.personal_accounts)
            to_account = random.choice(self.business_accounts + self.high_risk_accounts)
            amount = np.random.uniform(100, 5000)
            location = random.choice(["US", "EU"])
        
        elif fraud_type == "account_takeover":
            # Unusual time and location
            from_account = random.choice(self.personal_accounts)
            to_account = random.choice(self.high_risk_accounts)
            amount = np.random.uniform(1000, 25000)
            location = random.choice(["RU", "CN", "BR"])
        
        elif fraud_type == "duplicate_transaction":
            # Same transaction repeated
            from_account = random.choice(self.personal_accounts)
            to_account = random.choice(self.business_accounts)
            amount = np.random.uniform(100, 1000)
            location = random.choice(["US", "EU"])
        
        else:  # velocity_fraud
            # Multiple large transactions in short period
            from_account = random.choice(self.personal_accounts)
            to_account = random.choice(self.business_accounts)
            amount = np.random.uniform(500, 5000)
            location = random.choice(["US", "EU"])
        
        return {
            "transaction_id": transaction_id or str(uuid.uuid4()),
            "from_account": from_account,
            "to_account": to_account,
            "amount": round(amount, 2),
            "currency": random.choice(["USD", "EUR"]),
            "transaction_type": random.choice(list(TransactionType)),
            "timestamp": datetime.utcnow().isoformat(),
            "merchant_id": f"FRAUD-{random.randint(1000, 9999)}",
            "location": location,
            "device_id": f"DEV-{random.randint(1000, 9999)}",
            "is_weekend": random.choice([True, False]),
            "fraud_type": fraud_type,
            "label": 1  # Fraudulent
        }
    
    def generate_aml_transaction(self, transaction_id: str = None) -> Dict[str, Any]:
        """
        Generate a money laundering transaction.
        
        Returns:
            AML transaction dictionary
        """
        aml_type = random.choice([
            "structuring",
            "circular_flow",
            "layering",
            "integration"
        ])
        
        if aml_type == "structuring":
            # Smurfing: multiple small transactions to avoid reporting
            ring = random.choice(self.structuring_rings)
            idx = random.randint(0, len(ring) - 2)
            from_account = ring[idx]
            to_account = ring[idx + 1]
            amount = np.random.uniform(5000, 9999)  # Just below reporting threshold
        
        elif aml_type == "circular_flow":
            # Money flows in circle back to source
            network = random.choice(self.laundering_networks)
            idx = random.randint(0, len(network) - 1)
            from_account = network[idx]
            to_account = network[(idx + 1) % len(network)]
            amount = np.random.uniform(10000, 100000)
        
        elif aml_type == "layering":
            # Complex web of transactions
            network = random.choice(self.laundering_networks)
            from_account = random.choice(network)
            to_account = random.choice(self.business_accounts + self.high_risk_accounts)
            amount = np.random.uniform(50000, 500000)
        
        else:  # integration
            # Reintegration into financial system
            network = random.choice(self.laundering_networks)
            from_account = random.choice(network)
            to_account = random.choice(self.personal_accounts)
            amount = np.random.uniform(100000, 1000000)
        
        return {
            "transaction_id": transaction_id or str(uuid.uuid4()),
            "from_account": from_account,
            "to_account": to_account,
            "amount": round(amount, 2),
            "currency": random.choice(["USD", "EUR", "GBP", "HKD"]),
            "transaction_type": random.choice([TransactionType.WIRE_TRANSFER, 
                                             TransactionType.CURRENCY_EXCHANGE]),
            "timestamp": datetime.utcnow().isoformat(),
            "merchant_id": None,
            "location": random.choice(["RU", "CN", "HK", "AE", "PA"]),
            "device_id": f"DEV-{random.randint(1000, 9999)}",
            "is_weekend": False,
            "aml_type": aml_type,
            "is_aml": 1
        }
    
    def generate_batch(self, batch_size: int = 100, 
                      fraud_ratio: float = 0.05,
                      aml_ratio: float = 0.02) -> List[Dict[str, Any]]:
        """
        Generate a batch of transactions with specified fraud/AML ratios.
        
        Args:
            batch_size: Number of transactions to generate
            fraud_ratio: Fraction of fraudulent transactions (0.0-1.0)
            aml_ratio: Fraction of AML transactions (0.0-1.0)
            
        Returns:
            List of transaction dictionaries
        """
        num_fraud = int(batch_size * fraud_ratio)
        num_aml = int(batch_size * aml_ratio)
        num_normal = batch_size - num_fraud - num_aml
        
        batch = []
        
        # Add normal transactions
        for _ in range(num_normal):
            batch.append(self.generate_normal_transaction())
        
        # Add fraudulent transactions
        for _ in range(num_fraud):
            batch.append(self.generate_fraud_transaction())
        
        # Add AML transactions
        for _ in range(num_aml):
            batch.append(self.generate_aml_transaction())
        
        # Shuffle
        random.shuffle(batch)
        
        return batch
    
    def generate_stream(self, duration_seconds: int = 3600, 
                       transactions_per_second: float = 10,
                       fraud_ratio: float = 0.05,
                       aml_ratio: float = 0.02):
        """
        Generator that yields transactions as a stream.
        
        Args:
            duration_seconds: How long to stream for
            transactions_per_second: TPS rate
            fraud_ratio: Fraction of fraudulent transactions
            aml_ratio: Fraction of AML transactions
            
        Yields:
            Transaction dictionaries
        """
        start_time = datetime.utcnow()
        transaction_count = 0
        
        while True:
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            
            if elapsed > duration_seconds:
                break
            
            # Determine transaction type
            rand = random.random()
            if rand < aml_ratio:
                transaction = self.generate_aml_transaction()
            elif rand < aml_ratio + fraud_ratio:
                transaction = self.generate_fraud_transaction()
            else:
                transaction = self.generate_normal_transaction()
            
            yield transaction
            transaction_count += 1
            
            # Rate limiting
            time_per_transaction = 1.0 / transactions_per_second
            import time
            time.sleep(time_per_transaction)
        
        logger.info(f"Stream completed: generated {transaction_count} transactions")
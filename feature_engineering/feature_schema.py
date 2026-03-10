"""
Feature definitions and schemas for the fraud detection system.
Defines all features used by models.
"""
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class FeatureType(str, Enum):
    """Feature data types."""
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEMPORAL = "temporal"
    GRAPH = "graph"


@dataclass
class Feature:
    """Represents a single feature."""
    name: str
    feature_type: FeatureType
    description: str
    aggregation_window: str = None  # e.g., "1h", "24h", "7d"
    fillna_value: Any = None


class FeatureSchema:
    """Complete feature schema for all models."""
    
    # Transaction-level features
    TRANSACTION_FEATURES = [
        Feature("amount", FeatureType.NUMERICAL, "Transaction amount"),
        Feature("is_large_amount", FeatureType.NUMERICAL, "Whether amount > 10k"),
        Feature("is_high_risk_jurisdiction", FeatureType.NUMERICAL, "High-risk country"),
        Feature("hour_of_day", FeatureType.TEMPORAL, "Hour transaction occurred"),
        Feature("day_of_week", FeatureType.TEMPORAL, "Day of week (0-6)"),
        Feature("is_weekend", FeatureType.NUMERICAL, "Whether weekend"),
        Feature("transaction_type_encoded", FeatureType.CATEGORICAL, "Transaction type"),
    ]
    
    # Account features (from_account aggregations)
    ACCOUNT_FEATURES = [
        Feature("account_total_transactions_1h", FeatureType.NUMERICAL, 
               "Transactions from account in 1h", "1h"),
        Feature("account_total_amount_1h", FeatureType.NUMERICAL, 
               "Total amount from account in 1h", "1h"),
        Feature("account_avg_amount", FeatureType.NUMERICAL, 
               "Average transaction amount for account", "30d"),
        Feature("account_std_amount", FeatureType.NUMERICAL, 
               "Std dev of transaction amounts", "30d"),
        Feature("account_unique_recipients_1d", FeatureType.NUMERICAL, 
               "Unique recipients in 1d", "1d"),
        Feature("account_unique_recipients_7d", FeatureType.NUMERICAL, 
               "Unique recipients in 7d", "7d"),
        Feature("account_risk_score", FeatureType.NUMERICAL, 
               "Account historical risk score"),
    ]
    
    # Recipient features (to_account aggregations)
    RECIPIENT_FEATURES = [
        Feature("recipient_total_transactions_1h", FeatureType.NUMERICAL, 
               "Transactions to recipient in 1h", "1h"),
        Feature("recipient_total_amount_1h", FeatureType.NUMERICAL, 
               "Total amount to recipient in 1h", "1h"),
        Feature("recipient_avg_amount", FeatureType.NUMERICAL, 
               "Average amount recipient receives", "30d"),
        Feature("recipient_total_senders_1d", FeatureType.NUMERICAL, 
               "Unique senders in 1d", "1d"),
        Feature("recipient_total_senders_7d", FeatureType.NUMERICAL, 
               "Unique senders in 7d", "7d"),
        Feature("recipient_risk_score", FeatureType.NUMERICAL, 
               "Recipient historical risk score"),
    ]
    
    # Velocity features
    VELOCITY_FEATURES = [
        Feature("velocity_1h_count", FeatureType.NUMERICAL, 
               "Transactions from account in 1h", "1h"),
        Feature("velocity_1h_amount", FeatureType.NUMERICAL, 
               "Total amount from account in 1h", "1h"),
        Feature("velocity_24h_count", FeatureType.NUMERICAL, 
               "Transactions from account in 24h", "24h"),
        Feature("velocity_24h_amount", FeatureType.NUMERICAL, 
               "Total amount from account in 24h", "24h"),
        Feature("is_velocity_spike", FeatureType.NUMERICAL, 
               "Whether transaction rate anomalously high"),
    ]
    
    # Behavioral features
    BEHAVIORAL_FEATURES = [
        Feature("deviation_from_average_amount", FeatureType.NUMERICAL, 
               "Amount deviation from account average"),
        Feature("amount_z_score", FeatureType.NUMERICAL, 
               "Z-score of amount"),
        Feature("unusual_time_of_day", FeatureType.NUMERICAL, 
               "Whether unusual transaction time"),
        Feature("new_recipient_flag", FeatureType.NUMERICAL, 
               "Whether recipient is new to account"),
        Feature("new_geography_flag", FeatureType.NUMERICAL, 
               "Whether unusual geography"),
    ]
    
    # Graph/Network features
    GRAPH_FEATURES = [
        Feature("graph_clustering_coefficient", FeatureType.GRAPH, 
               "Clustering coefficient in network"),
        Feature("graph_degree_centrality", FeatureType.GRAPH, 
               "Degree centrality in network"),
        Feature("graph_betweenness_centrality", FeatureType.GRAPH, 
               "Betweenness centrality"),
        Feature("is_in_suspicious_network", FeatureType.GRAPH, 
               "Whether account is in known suspicious network"),
        Feature("network_risk_propagation_score", FeatureType.GRAPH, 
               "Aggregated risk from network"),
        Feature("circular_flow_likelihood", FeatureType.GRAPH, 
               "Likelihood of circular money flow"),
        Feature("layering_pattern_score", FeatureType.GRAPH, 
               "Score for AML layering pattern"),
    ]
    
    # All features combined
    ALL_FEATURES = (
        TRANSACTION_FEATURES +
        ACCOUNT_FEATURES +
        RECIPIENT_FEATURES +
        VELOCITY_FEATURES +
        BEHAVIORAL_FEATURES +
        GRAPH_FEATURES
    )
    
    @classmethod
    def get_numerical_features(cls) -> List[str]:
        """Get names of all numerical features."""
        return [f.name for f in cls.ALL_FEATURES 
                if f.feature_type == FeatureType.NUMERICAL]
    
    @classmethod
    def get_categorical_features(cls) -> List[str]:
        """Get names of all categorical features."""
        return [f.name for f in cls.ALL_FEATURES 
                if f.feature_type == FeatureType.CATEGORICAL]
    
    @classmethod
    def get_temporal_features(cls) -> List[str]:
        """Get names of all temporal features."""
        return [f.name for f in cls.ALL_FEATURES 
                if f.feature_type == FeatureType.TEMPORAL]
    
    @classmethod
    def get_graph_features(cls) -> List[str]:
        """Get names of all graph features."""
        return [f.name for f in cls.ALL_FEATURES 
                if f.feature_type == FeatureType.GRAPH]
    
    @classmethod
    def feature_schema_dict(cls) -> Dict[str, Dict[str, Any]]:
        """Get feature schema as dictionary."""
        schema = {}
        for feature in cls.ALL_FEATURES:
            schema[feature.name] = {
                "type": feature.feature_type.value,
                "description": feature.description,
                "aggregation_window": feature.aggregation_window,
                "fillna_value": feature.fillna_value
            }
        return schema
"""
Unsupervised anomaly detection using Isolation Forest.
"""
import logging
import pickle
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from feature_engineering.feature_schema import FeatureSchema

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Isolation Forest-based anomaly detector."""
    
    def __init__(self, contamination: float = 0.05, model_path: str = None):
        """
        Initialize anomaly detector.
        
        Args:
            contamination: Expected fraction of outliers
            model_path: Path to saved model
        """
        self.contamination = contamination
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = FeatureSchema.get_numerical_features()
        
        if model_path:
            self.load(model_path)
    
    def train(self, X_train: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the anomaly detector.
        
        Args:
            X_train: Training features (unlabeled)
            
        Returns:
            Training results
        """
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Train Isolation Forest
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1,
            n_estimators=100
        )
        self.model.fit(X_train_scaled)
        
        logger.info("Anomaly detector trained successfully")
        
        return {
            "model_type": "IsolationForest",
            "training_samples": len(X_train),
            "contamination": self.contamination,
            "feature_count": len(X_train.columns)
        }
    
    def predict_proba(self, features: Dict[str, Any]) -> Tuple[float, float]:
        """
        Predict anomaly probability for a transaction.
        
        Args:
            features: Transaction features
            
        Returns:
            Tuple of (normal_prob, anomaly_prob)
        """
        if not self.model:
            return (0.5, 0.5)
        
        # Extract relevant features
        feature_vector = np.array([features.get(name, 0) for name in self.feature_names])
        feature_vector = feature_vector.reshape(1, -1)
        
        # Scale
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Predict
        anomaly_score = self.model.decision_function(feature_vector_scaled)[0]
        
        # Convert to probability (between 0 and 1)
        anomaly_prob = 1.0 / (1.0 + np.exp(-anomaly_score))
        normal_prob = 1 - anomaly_prob
        
        return (normal_prob, anomaly_prob)
    
    def save(self, path: str):
        """Save model to disk."""
        with open(path, 'wb') as f:
            pickle.dump({'model': self.model, 'scaler': self.scaler}, f)
        logger.info(f"Model saved to {path}")
    
    def load(self, path: str):
        """Load model from disk."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
        logger.info(f"Model loaded from {path}")
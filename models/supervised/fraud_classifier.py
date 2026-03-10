"""
Supervised fraud classification model using XGBoost.
"""
import logging
import pickle
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import xgboost as xgb # type: ignore
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from feature_engineering.feature_schema import FeatureSchema

logger = logging.getLogger(__name__)


class FraudClassifier:
    """XGBoost-based fraud classifier."""
    
    def __init__(self, model_path: str = None):
        """
        Initialize fraud classifier.
        
        Args:
            model_path: Path to saved model
        """
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = FeatureSchema.get_numerical_features()
        
        if model_path:
            self.load(model_path)
    
    def train(self, X_train: pd.DataFrame, y_train: pd.Series,
             X_val: pd.DataFrame = None, y_val: pd.Series = None) -> Dict[str, Any]:
        """
        Train the fraud classifier.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            
        Returns:
            Training results
        """
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        
        # Create XGBoost dataset
        dtrain = xgb.DMatrix(X_train_scaled, label=y_train)
        
        params = {
            'objective': 'binary:logistic',
            'max_depth': 6,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'min_child_weight': 1,
            'gamma': 0,
            'scale_pos_weight': len(y_train[y_train==0]) / len(y_train[y_train==1])
        }
        
        evals = []
        if X_val is not None and y_val is not None:
            X_val_scaled = self.scaler.transform(X_val)
            dval = xgb.DMatrix(X_val_scaled, label=y_val)
            evals = [(dtrain, 'train'), (dval, 'val')]
        
        self.model = xgb.train(
            params,
            dtrain,
            num_boost_round=100,
            evals=evals,
            early_stopping_rounds=10,
            verbose_eval=10
        )
        
        logger.info("Fraud classifier trained successfully")
        
        return {
            "model_type": "XGBoost",
            "training_samples": len(X_train),
            "feature_count": len(X_train.columns)
        }
    
    def predict_proba(self, features: Dict[str, Any]) -> Tuple[float, float]:
        """
        Predict fraud probability for a transaction.
        
        Args:
            features: Transaction features
            
        Returns:
            Tuple of (normal_prob, fraud_prob)
        """
        if not self.model:
            return (0.5, 0.5)
        
        # Extract relevant features
        feature_vector = np.array([features.get(name, 0) for name in self.feature_names])
        feature_vector = feature_vector.reshape(1, -1)
        
        # Scale
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Predict
        dmatrix = xgb.DMatrix(feature_vector_scaled)
        fraud_prob = self.model.predict(dmatrix)[0]
        normal_prob = 1 - fraud_prob
        
        return (normal_prob, fraud_prob)
    
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
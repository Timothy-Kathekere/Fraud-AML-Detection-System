"""
Ensemble scoring combining all three model types.
"""
import logging
from typing import Dict, Any, Tuple
import numpy as np
from config.settings import settings

logger = logging.getLogger(__name__)


class EnsembleScorer:
    """Combines predictions from supervised, unsupervised, and graph models."""
    
    def __init__(self, supervised_model=None, unsupervised_model=None, graph_model=None):
        """
        Initialize ensemble scorer.
        
        Args:
            supervised_model: Fraud classifier model
            unsupervised_model: Anomaly detector model
            graph_model: Graph-based AML detector
        """
        self.supervised_model = supervised_model
        self.unsupervised_model = unsupervised_model
        self.graph_model = graph_model
        
        # Weights for ensemble
        self.supervised_weight = 0.4
        self.unsupervised_weight = 0.3
        self.graph_weight = 0.3
    
    def score_transaction(self, features: Dict[str, Any], 
                        graph_features: Dict[str, Any] = None) -> Tuple[float, Dict[str, Any]]:
        """
        Score a transaction using ensemble of models.
        
        Args:
            features: Transaction features
            graph_features: Graph-based features
            
        Returns:
            Tuple of (risk_score, scores_breakdown)
        """
        scores = {}
        
        # Supervised model score (fraud detection)
        if self.supervised_model:
            try:
                supervised_score = self.supervised_model.predict_proba(features)[1]
                scores["supervised"] = float(supervised_score)
            except Exception as e:
                logger.error(f"Error in supervised scoring: {str(e)}")
                scores["supervised"] = 0.5
        else:
            scores["supervised"] = 0.5
        
        # Unsupervised model score (anomaly detection)
        if self.unsupervised_model:
            try:
                unsupervised_score = self.unsupervised_model.predict_proba(features)[1]
                scores["unsupervised"] = float(unsupervised_score)
            except Exception as e:
                logger.error(f"Error in unsupervised scoring: {str(e)}")
                scores["unsupervised"] = 0.5
        else:
            scores["unsupervised"] = 0.5
        
        # Graph model score (AML detection)
        if self.graph_model and graph_features:
            try:
                graph_score = self.graph_model.score_transaction(graph_features)
                scores["graph"] = float(graph_score)
            except Exception as e:
                logger.error(f"Error in graph scoring: {str(e)}")
                scores["graph"] = 0.5
        else:
            scores["graph"] = 0.5
        
        # Weighted ensemble
        ensemble_score = (
            self.supervised_weight * scores["supervised"] +
            self.unsupervised_weight * scores["unsupervised"] +
            self.graph_weight * scores["graph"]
        )
        
        return ensemble_score, scores
    
    def update_weights(self, supervised: float, unsupervised: float, graph: float):
        """Update model weights in ensemble."""
        total = supervised + unsupervised + graph
        self.supervised_weight = supervised / total
        self.unsupervised_weight = unsupervised / total
        self.graph_weight = graph / total
        logger.info(f"Updated ensemble weights: {self.supervised_weight:.2f}, {self.unsupervised_weight:.2f}, {self.graph_weight:.2f}")
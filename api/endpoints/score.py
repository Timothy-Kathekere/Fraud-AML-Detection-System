"""
Real-time scoring endpoint for single transactions.
"""
import logging
import time
from fastapi import APIRouter, HTTPException
from api.schemas import TransactionRequest, TransactionResponse
from feature_engineering.feature_extractor import FeatureExtractor
from feature_engineering.cache_manager import CacheManager
from models.ensemble.ensemble_scorer import EnsembleScorer
from graph_detection.pattern_detector import PatternDetector # type: ignore
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize components (these would be loaded from dependency injection)
cache_manager = CacheManager()
feature_extractor = FeatureExtractor(cache_manager)
ensemble_scorer = EnsembleScorer()
pattern_detector = PatternDetector()


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


def get_risk_level(score: float) -> str:
    """Determine risk level from score."""
    if score < 0.4:
        return RiskLevel.LOW.value
    elif score < 0.6:
        return RiskLevel.MEDIUM.value
    elif score < 0.8:
        return RiskLevel.HIGH.value
    else:
        return RiskLevel.CRITICAL.value


@router.post("/score", response_model=TransactionResponse)
async def score_transaction(transaction: TransactionRequest) -> TransactionResponse:
    """
    Score a single transaction for fraud/AML risk.
    
    <100ms latency target
    """
    start_time = time.time()
    
    try:
        # Extract features
        features = feature_extractor.extract_features(transaction.dict())
        
        # Get graph features
        graph_features = pattern_detector.extract_graph_features(
            transaction.from_account,
            transaction.to_account
        )
        
        # Score with ensemble
        risk_score, scores = ensemble_scorer.score_transaction(features, graph_features)
        
        # Determine risk level
        risk_level = get_risk_level(risk_score)
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Scored transaction {transaction.transaction_id}: {risk_score:.3f} ({risk_level})")
        
        return TransactionResponse(
            transaction_id=transaction.transaction_id,
            risk_score=float(risk_score),
            risk_level=risk_level,
            fraud_probability=float(scores.get("supervised", 0)),
            anomaly_probability=float(scores.get("unsupervised", 0)),
            aml_probability=float(scores.get("graph", 0)),
            scores=scores,
            features_used=len(features),
            processing_time_ms=processing_time_ms,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error scoring transaction: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
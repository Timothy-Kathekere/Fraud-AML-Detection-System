"""
Pydantic schemas for API request/response models.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TransactionRequest(BaseModel):
    """Single transaction scoring request."""
    transaction_id: str = Field(..., description="Unique transaction ID")
    from_account: str = Field(..., description="Sender account ID")
    to_account: str = Field(..., description="Recipient account ID")
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code")
    transaction_type: str = Field(default="TRANSFER", description="Transaction type")
    timestamp: Optional[str] = Field(default=None, description="ISO format timestamp")
    merchant_id: Optional[str] = None
    location: Optional[str] = None
    device_id: Optional[str] = None


class TransactionResponse(BaseModel):
    """Single transaction scoring response."""
    transaction_id: str
    risk_score: float = Field(..., ge=0, le=1)
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    fraud_probability: float
    anomaly_probability: float
    aml_probability: float
    scores: Dict[str, float]
    features_used: int
    processing_time_ms: float
    timestamp: datetime


class BatchScoringRequest(BaseModel):
    """Batch scoring request."""
    transactions: List[TransactionRequest]
    include_details: bool = False


class BatchScoringResponse(BaseModel):
    """Batch scoring response."""
    batch_id: str
    total_transactions: int
    processed_transactions: int
    failed_transactions: int
    high_risk_count: int
    processing_time_ms: float
    results: Optional[List[TransactionResponse]] = None


class AlertRequest(BaseModel):
    """Alert creation request."""
    transaction_id: str
    risk_score: float
    alert_type: str  # FRAUD, AML, SUSPICIOUS_ACTIVITY
    reason: str
    affected_accounts: List[str]


class AlertResponse(BaseModel):
    """Alert response."""
    alert_id: str
    transaction_id: str
    status: str  # OPEN, INVESTIGATING, CLOSED
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    models_loaded: bool
    database_connected: bool
    cache_connected: bool
    timestamp: datetime


class DashboardMetrics(BaseModel):
    """Dashboard metrics."""
    total_transactions_24h: int
    fraud_detections_24h: int
    aml_alerts_24h: int
    avg_fraud_score: float
    model_accuracy: float
    api_latency_p99: float
    cache_hit_rate: float
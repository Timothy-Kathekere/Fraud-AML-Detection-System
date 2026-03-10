"""
SQLAlchemy ORM models for fraud detection system.
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Transaction(Base):
    """Transaction table."""
    __tablename__ = "transactions"
    
    transaction_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_account = Column(String, nullable=False, index=True)
    to_account = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    transaction_type = Column(String)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    merchant_id = Column(String)
    location = Column(String)
    device_id = Column(String)
    
    # Fraud/AML labels
    label = Column(Integer, default=0)  # 0: legitimate, 1: fraud
    is_aml = Column(Integer, default=0)  # 0: legitimate, 1: AML
    
    # Risk scores
    fraud_score = Column(Float, default=0.0)
    anomaly_score = Column(Float, default=0.0)
    aml_score = Column(Float, default=0.0)
    ensemble_risk_score = Column(Float, default=0.0)
    
    # Processing
    processed_at = Column(DateTime, default=datetime.utcnow)
    processing_version = Column(String)
    
    # Relationships
    alerts = relationship("Alert", back_populates="transaction")
    
    def __repr__(self):
        return f"<Transaction {self.transaction_id}: {self.from_account}->{self.to_account} {self.amount}>"


class Alert(Base):
    """Alert table."""
    __tablename__ = "alerts"
    
    alert_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    transaction_id = Column(String, ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    alert_type = Column(String, nullable=False)  # FRAUD, AML, SUSPICIOUS_ACTIVITY
    risk_score = Column(Float, nullable=False)
    reason = Column(String)
    affected_accounts = Column(JSON)
    
    status = Column(String, default="OPEN", index=True)  # OPEN, INVESTIGATING, CLOSED, RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    # Investigation
    case_id = Column(String, ForeignKey("cases.case_id"))
    investigator_notes = Column(String)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="alerts")
    case = relationship("Case", back_populates="alerts")
    
    def __repr__(self):
        return f"<Alert {self.alert_id}: {self.alert_type} ({self.status})>"


class Case(Base):
    """Investigation case table."""
    __tablename__ = "cases"
    
    case_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    case_type = Column(String)  # FRAUD, AML, SUSPICIOUS_ACTIVITY
    
    primary_account = Column(String, index=True)
    related_accounts = Column(JSON)
    
    status = Column(String, default="OPEN", index=True)  # OPEN, INVESTIGATING, CLOSED, RESOLVED
    priority = Column(String, default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime)
    
    # Investigation details
    assigned_to = Column(String)
    description = Column(String)
    findings = Column(JSON)
    resolution = Column(String)
    
    # Relationships
    alerts = relationship("Alert", back_populates="case")
    
    def __repr__(self):
        return f"<Case {self.case_id}: {self.case_type} ({self.status})>"


class Account(Base):
    """Account profile table."""
    __tablename__ = "accounts"
    
    account_id = Column(String, primary_key=True)
    account_type = Column(String)  # PERSONAL, BUSINESS, HIGH_RISK_JURISDICTION
    
    # Risk profile
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String, default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    
    # Activity metrics
    total_transactions = Column(Integer, default=0)
    total_volume = Column(Float, default=0.0)
    avg_transaction_amount = Column(Float, default=0.0)
    
    # Network metrics
    unique_counterparties = Column(Integer, default=0)
    network_centrality = Column(Float, default=0.0)
    
    # Flags
    is_blacklisted = Column(Boolean, default=False)
    is_high_risk = Column(Boolean, default=False)
    requires_kyc = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime)
    
    def __repr__(self):
        return f"<Account {self.account_id}: {self.account_type} ({self.risk_level})>"


class GraphEdge(Base):
    """Transaction network edges."""
    __tablename__ = "graph_edges"
    
    edge_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_account = Column(String, index=True)
    to_account = Column(String, index=True)
    
    # Edge metrics
    transaction_count = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    avg_amount = Column(Float, default=0.0)
    
    # Risk
    edge_risk_score = Column(Float, default=0.0)
    
    # Timing
    first_transaction = Column(DateTime)
    last_transaction = Column(DateTime)
    
    # Patterns
    detected_patterns = Column(JSON)  # List of detected patterns
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<GraphEdge {self.from_account}->{self.to_account}>"


class ModelPerformance(Base):
    """Track model performance metrics."""
    __tablename__ = "model_performance"
    
    metric_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String, index=True)
    model_version = Column(String)
    
    # Classification metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    auc_roc = Column(Float)
    
    # Validation data
    validation_samples = Column(Integer)
    false_positives = Column(Integer)
    false_negatives = Column(Integer)
    true_positives = Column(Integer)
    true_negatives = Column(Integer)
    
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ModelPerformance {self.model_name} v{self.model_version}>"


class RetrainingLog(Base):
    """Log of model retraining events."""
    __tablename__ = "retraining_log"
    
    log_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    model_name = Column(String, index=True)
    
    training_start = Column(DateTime, default=datetime.utcnow)
    training_end = Column(DateTime)
    
    # Training data
    training_samples = Column(Integer)
    validation_samples = Column(Integer)
    fraud_samples = Column(Integer)
    
    # Results
    previous_version = Column(String)
    new_version = Column(String)
    performance_improvement = Column(Float)
    
    status = Column(String)  # SUCCESS, FAILED, INCOMPLETE
    notes = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<RetrainingLog {self.model_name} ({self.status})>"
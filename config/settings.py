"""
Configuration management for the fraud detection system.
"""
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from pathlib import Path


class KafkaSettings(BaseSettings):
    """Kafka configuration."""
    bootstrap_servers: str = "localhost:9092"
    topic_transactions: str = "transactions"
    topic_alerts: str = "alerts"
    consumer_group: str = "fraud-detection-group"
    max_poll_records: int = 500


class DatabaseSettings(BaseSettings):
    """PostgreSQL configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "fraud_detection"
    user: str = "postgres"
    password: str = "postgres"
    pool_size: int = 20
    max_overflow: int = 40
    echo: bool = False
    
    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisSettings(BaseSettings):
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    ttl_seconds: int = 3600
    max_connections: int = 50


class ModelSettings(BaseSettings):
    """Model configuration."""
    fraud_threshold: float = 0.6
    anomaly_threshold: float = 0.7
    graph_risk_threshold: float = 0.65
    ensemble_method: str = "weighted_avg"  # weighted_avg, voting, stacking
    model_version: str = "v1.0"
    
    # Supervised model
    supervised_model_path: str = "models/supervised/model_artifacts/fraud_classifier.pkl"
    supervised_threshold: float = 0.6
    
    # Unsupervised model
    unsupervised_model_path: str = "models/unsupervised/model_artifacts/anomaly_detector.pkl"
    unsupervised_threshold: float = 0.7
    
    # Graph model
    graph_model_path: str = "models/graph_based/model_artifacts/graph_model.pkl"
    
    retraining_interval_days: int = 7
    min_samples_for_retraining: int = 10000


class APISettings(BaseSettings):
    """API configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    max_request_size: int = 10_000_000
    request_timeout: int = 30
    
    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 1000
    rate_limit_period: int = 60


class AlertSettings(BaseSettings):
    """Alert configuration."""
    enabled: bool = True
    batch_alert_interval_seconds: int = 60
    high_risk_threshold: float = 0.8
    medium_risk_threshold: float = 0.6
    low_risk_threshold: float = 0.4
    
    # Notifications
    send_email_alerts: bool = True
    email_recipients: List[str] = ["alerts@company.com"]
    send_slack_alerts: bool = True
    slack_webhook_url: Optional[str] = None
    send_webhook_alerts: bool = True
    webhook_url: Optional[str] = None


class MonitoringSettings(BaseSettings):
    """Monitoring configuration."""
    prometheus_enabled: bool = True
    prometheus_port: int = 8001
    log_level: str = "INFO"
    enable_request_logging: bool = True
    enable_query_logging: bool = True
    metrics_update_interval_seconds: int = 60


class Settings(BaseSettings):
    """Main settings class combining all configurations."""
    environment: str = "development"  # development, staging, production
    debug: bool = False
    
    # Component settings
    kafka: KafkaSettings = KafkaSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    models: ModelSettings = ModelSettings()
    api: APISettings = APISettings()
    alerts: AlertSettings = AlertSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    
    # System settings
    batch_size: int = 32
    num_workers: int = 4
    latency_budget_ms: int = 100
    max_batch_delay_ms: int = 50
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


# Global settings instance
settings = Settings()
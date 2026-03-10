"""
Prometheus monitoring setup and metrics.
"""
import logging
from prometheus_client import Counter, Histogram, Gauge, start_http_server # type: ignore
from config.settings import settings

logger = logging.getLogger(__name__)

# Transaction metrics
transactions_processed = Counter(
    'transactions_processed_total',
    'Total transactions processed',
    ['status']
)

fraud_scores = Histogram(
    'fraud_scores',
    'Distribution of fraud scores',
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# API metrics
api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0]
)

# Cache metrics
cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits'
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses'
)

# Database metrics
db_connections = Gauge(
    'database_connections_active',
    'Active database connections'
)

# Model metrics
model_inference_time = Histogram(
    'model_inference_time_seconds',
    'Model inference time',
    ['model_type'],
    buckets=[0.01, 0.02, 0.05, 0.1]
)

alerts_generated = Counter(
    'alerts_generated_total',
    'Total alerts generated',
    ['alert_type', 'severity']
)


def setup_prometheus():
    """Setup Prometheus metrics server."""
    try:
        if settings.monitoring.prometheus_enabled:
            start_http_server(settings.monitoring.prometheus_port)
            logger.info(f"Prometheus metrics server started on port {settings.monitoring.prometheus_port}")
    except Exception as e:
        logger.error(f"Error starting Prometheus: {str(e)}")
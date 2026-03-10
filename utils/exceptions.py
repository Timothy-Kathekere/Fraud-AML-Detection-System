"""
Custom exceptions for the fraud detection system.
"""


class FraudDetectionException(Exception):
    """Base exception for the fraud detection system."""
    pass


class DataPipelineException(FraudDetectionException):
    """Exception raised in data pipeline operations."""
    pass


class FeatureEngineeringException(FraudDetectionException):
    """Exception raised in feature engineering."""
    pass


class ModelException(FraudDetectionException):
    """Exception raised in model operations."""
    pass


class APIException(FraudDetectionException):
    """Exception raised in API operations."""
    pass


class DatabaseException(FraudDetectionException):
    """Exception raised in database operations."""
    pass


class AlertException(FraudDetectionException):
    """Exception raised in alert system."""
    pass


class CacheException(FraudDetectionException):
    """Exception raised in caching operations."""
    pass


class InvalidTransactionException(DataPipelineException):
    """Exception raised for invalid transaction data."""
    pass


class ModelNotLoadedException(ModelException):
    """Exception raised when model cannot be loaded."""
    pass


class ScoringTimeoutException(APIException):
    """Exception raised when scoring exceeds timeout."""
    pass
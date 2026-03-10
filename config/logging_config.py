"""
Logging configuration for the fraud detection system.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger # type: ignore
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_dir: str = "logs") -> None:
    """
    Configure logging with both console and file handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
    """
    # Create logs directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler (standard format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (JSON format for structured logging)
    file_handler = RotatingFileHandler(
        filename=f"{log_dir}/fraud_detection.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    json_formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_handler = RotatingFileHandler(
        filename=f"{log_dir}/fraud_detection_errors.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=10
    )
    error_handler.setLevel("ERROR")
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)
    
    logging.info(f"Logging configured at level {log_level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
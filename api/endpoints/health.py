"""
Health check endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException
from datetime import datetime
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": settings.environment
    }


@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check with service status."""
    from feature_engineering.cache_manager import CacheManager
    from database.db_manager import DatabaseManager
    
    health_status = {
        "api": "healthy",
        "database": "unknown",
        "cache": "unknown",
        "models": "unknown",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check database
    try:
        db = DatabaseManager()
        if db.health_check():
            health_status["database"] = "healthy"
        else:
            health_status["database"] = "unhealthy"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        logger.error(f"Database health check failed: {str(e)}")
    
    # Check cache
    try:
        cache = CacheManager()
        info = cache.get_stats()
        if info:
            health_status["cache"] = "healthy"
        else:
            health_status["cache"] = "unhealthy"
    except Exception as e:
        health_status["cache"] = f"error: {str(e)}"
        logger.error(f"Cache health check failed: {str(e)}")
    
    return health_status
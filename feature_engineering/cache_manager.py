"""
Redis-based cache manager for feature caching and real-time aggregations.
"""
import json
import logging
from typing import Any, Optional, Dict, List
import redis # type: ignore
import asyncio
from config.settings import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of features and aggregations in Redis."""
    
    def __init__(self):
        """Initialize Redis cache."""
        self.redis_client = redis.Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            decode_responses=True,
            max_connections=settings.redis.max_connections,
            socket_keepalive=True
        )
        
        # Test connection
        try:
            self.redis_client.ping()
            logger.info("Cache manager connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            ttl = ttl or settings.redis.ttl_seconds
            
            if isinstance(value, dict):
                value = json.dumps(value)
            elif not isinstance(value, str):
                value = str(value)
            
            self.redis_client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        try:
            value = self.redis_client.get(key)
            
            if value is None:
                return None
            
            # Try to parse as JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs
        """
        try:
            values = self.redis_client.mget(keys)
            result = {}
            
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            
            return result
        except Exception as e:
            logger.error(f"Error getting multiple cache keys: {str(e)}")
            return {}
    
    def increment(self, key: str, amount: int = 1, ttl: int = None) -> int:
        """
        Increment numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment
            ttl: Time to live if key is new
            
        Returns:
            New value
        """
        try:
            # Check if key exists
            exists = self.redis_client.exists(key)
            
            value = self.redis_client.incrby(key, amount)
            
            # Set TTL if key is new
            if not exists and ttl:
                self.redis_client.expire(key, ttl)
            
            return value
        except Exception as e:
            logger.error(f"Error incrementing cache key {key}: {str(e)}")
            return 0
    
    def add_to_set(self, key: str, value: str, ttl: int = None) -> int:
        """
        Add value to a set in cache.
        
        Args:
            key: Cache key
            value: Value to add
            ttl: Time to live
            
        Returns:
            Number of elements added
        """
        try:
            ttl = ttl or settings.redis.ttl_seconds
            
            count = self.redis_client.sadd(key, value)
            self.redis_client.expire(key, ttl)
            
            return count
        except Exception as e:
            logger.error(f"Error adding to set {key}: {str(e)}")
            return 0
    
    def get_set_size(self, key: str) -> int:
        """Get size of set."""
        try:
            return self.redis_client.scard(key)
        except Exception as e:
            logger.error(f"Error getting set size {key}: {str(e)}")
            return 0
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache."""
        try:
            self.redis_client.flushdb()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            info = self.redis_client.info()
            return {
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace": info.get("db0", {})
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {}
    
    def close(self):
        """Close Redis connection."""
        try:
            self.redis_client.close()
            logger.info("Cache connection closed")
        except Exception as e:
            logger.error(f"Error closing cache: {str(e)}")
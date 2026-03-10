"""
Decorators for performance monitoring and error handling.
"""
import functools
import time
import logging
from typing import Callable, Any
from prometheus_client import Counter, Histogram, Gauge # type: ignore
import asyncio


logger = logging.getLogger(__name__)

# Prometheus metrics
function_calls = Counter(
    'function_calls_total',
    'Total function calls',
    ['function_name', 'status']
)

function_duration = Histogram(
    'function_duration_seconds',
    'Function execution duration',
    ['function_name'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0)
)

active_function_calls = Gauge(
    'active_function_calls',
    'Active function calls',
    ['function_name']
)


def monitor_performance(func: Callable) -> Callable:
    """
    Decorator to monitor function performance and track metrics.
    
    Args:
        func: Function to monitor
        
    Returns:
        Wrapped function with monitoring
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        func_name = func.__name__
        active_function_calls.labels(function_name=func_name).inc()
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            function_calls.labels(function_name=func_name, status='success').inc()
            return result
        except Exception as e:
            function_calls.labels(function_name=func_name, status='error').inc()
            logger.error(f"Error in {func_name}: {str(e)}")
            raise
        finally:
            duration = time.time() - start_time
            function_duration.labels(function_name=func_name).observe(duration)
            active_function_calls.labels(function_name=func_name).dec()
            
            if duration > 0.1:  # Log slow functions
                logger.warning(f"{func_name} took {duration:.3f}s")
    
    return wrapper


def async_monitor_performance(func: Callable) -> Callable:
    """
    Async version of monitor_performance decorator.
    
    Args:
        func: Async function to monitor
        
    Returns:
        Wrapped async function with monitoring
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        func_name = func.__name__
        active_function_calls.labels(function_name=func_name).inc()
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            function_calls.labels(function_name=func_name, status='success').inc()
            return result
        except Exception as e:
            function_calls.labels(function_name=func_name, status='error').inc()
            logger.error(f"Error in {func_name}: {str(e)}")
            raise
        finally:
            duration = time.time() - start_time
            function_duration.labels(function_name=func_name).observe(duration)
            active_function_calls.labels(function_name=func_name).dec()
            
            if duration > 0.1:
                logger.warning(f"{func_name} took {duration:.3f}s")
    
    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0) -> Callable:
    """
    Decorator to retry a function on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries
        backoff: Backoff multiplier for delay
        
    Returns:
        Wrapped function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}, "
                            f"retrying in {current_delay}s: {str(e)}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator


def timeout(seconds: int) -> Callable:
    """
    Decorator to enforce function timeout.
    
    Args:
        seconds: Timeout in seconds
        
    Returns:
        Wrapped function with timeout
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            def target():
                return func(*args, **kwargs)
            
            import threading
            result = [None]
            exception = [None]
            
            def execute():
                try:
                    result[0] = target()
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=execute)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)
            
            if thread.is_alive():
                logger.error(f"{func.__name__} exceeded timeout of {seconds}s")
                raise TimeoutError(f"Function {func.__name__} timed out after {seconds}s")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        
        return wrapper
    return decorator
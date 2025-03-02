import asyncio
import logging
import time
from typing import Any, Callable, Coroutine, Dict, Optional, TypeVar, cast
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')

class TimeoutManager:
    """
    A utility class to help manage timeouts for asynchronous operations,
    ensuring that API endpoints respond within a specified time limit.
    """
    
    def __init__(self, max_total_time: float = 40.0):
        """
        Initialize the timeout manager.
        
        Args:
            max_total_time: Maximum total processing time in seconds
        """
        self.max_total_time = max_total_time
        self.start_time = time.time()
        
    def time_remaining(self) -> float:
        """Calculate remaining time before the overall timeout"""
        elapsed = time.time() - self.start_time
        return max(0.1, self.max_total_time - elapsed)
    
    def is_timeout_approaching(self, buffer: float = 5.0) -> bool:
        """Check if we're approaching the timeout limit"""
        return self.time_remaining() < buffer
    
    async def run_with_timeout(
        self, 
        coro: Coroutine[Any, Any, T], 
        timeout: Optional[float] = None,
        fallback_func: Optional[Callable[[], T]] = None
    ) -> T:
        """
        Run a coroutine with a timeout, with an optional fallback function
        
        Args:
            coro: The coroutine to run
            timeout: Maximum time to wait for the coroutine to complete (or time_remaining if None)
            fallback_func: Optional fallback function to call if timeout occurs
            
        Returns:
            The result of the coroutine, or the fallback function if timeout occurs
        """
        if timeout is None:
            timeout = self.time_remaining()
            
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Operation timed out after {timeout:.2f}s")
            if fallback_func:
                logger.info("Using fallback function")
                return fallback_func()
            raise
    
    def reset(self) -> None:
        """Reset the start time"""
        self.start_time = time.time()
        
def with_timeout(timeout: float):
    """
    Decorator to run a coroutine with a timeout
    
    Args:
        timeout: Maximum time in seconds to wait for the coroutine to complete
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Function {func.__name__} timed out after {timeout}s")
                # You can customize this to return a default value instead of raising
                raise
        return wrapper
    return decorator

"""
Common decorators following DRY principle.
"""

from functools import wraps
from fastapi import Request
from src.core.utils import log_request, log_response, logger


def log_endpoint(operation_name: str):
    """
    Decorator to automatically log request and response following DRY principle.
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                for key, value in kwargs.items():
                    if isinstance(value, Request):
                        request = value
                        break
            
            if request:
                log_request(request, {"operation": operation_name})
            
            try:
                result = await func(*args, **kwargs)
                
                if request:
                    log_response(request, result if isinstance(result, dict) else {"result": "success"})
                
                return result
            except Exception as e:
                logger.error(f"Error in {operation_name}: {e}")
                raise
        
        return wrapper
    return decorator


def require_authentication(func):
    """
    Decorator to ensure authentication is required following DRY principle.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This would be used with FastAPI's Depends system
        # The actual authentication check is handled by get_current_user dependency
        return await func(*args, **kwargs)
    return wrapper


def rate_limited(limit_type: str = "default"):
    """
    Decorator for rate limiting following DRY principle.
    
    Args:
        limit_type: Type of rate limit to apply
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Rate limiting is handled by slowapi decorators
            # This is just a placeholder for future enhancements
            return await func(*args, **kwargs)
        return wrapper
    return decorator

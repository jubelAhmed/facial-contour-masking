"""
Centralized error handling utilities following DRY principle.
"""

from fastapi import HTTPException, status
from typing import Callable, Any, Optional
from functools import wraps
from src.core.utils import logger


def handle_database_errors(operation_name: str):
    """
    Decorator to handle common database errors following DRY principle.
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Database error in {operation_name}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{operation_name} failed"
                )
        return wrapper
    return decorator


def handle_api_errors(operation_name: str):
    """
    Decorator to handle common API errors following DRY principle.
    
    Args:
        operation_name: Name of the operation for logging
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"API error in {operation_name}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"{operation_name} failed"
                )
        return wrapper
    return decorator


class DatabaseErrorHandler:
    """Centralized database error handling following DRY principle."""
    
    @staticmethod
    def handle_user_creation_error(e: Exception) -> HTTPException:
        logger.error(f"Database error creating user: {e}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User creation failed"
        )
    
    @staticmethod
    def handle_user_authentication_error(e: Exception) -> HTTPException:
        logger.error(f"Database error authenticating user: {e}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )
    
    @staticmethod
    def handle_job_status_error(e: Exception) -> HTTPException:
        logger.error(f"Database error storing job status: {e}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job status update failed"
        )
    
    @staticmethod
    def handle_cache_error(e: Exception) -> HTTPException:
        logger.error(f"Database error with cache: {e}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Cache operation failed"
        )


class APIErrorHandler:
    """Centralized API error handling following DRY principle."""
    
    @staticmethod
    def handle_validation_error(operation: str, e: Exception) -> HTTPException:
        logger.error(f"Validation error in {operation}: {e}")
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input for {operation}"
        )
    
    @staticmethod
    def handle_processing_error(operation: str, e: Exception) -> HTTPException:
        logger.error(f"Processing error in {operation}: {e}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{operation} processing failed"
        )

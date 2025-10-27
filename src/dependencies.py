"""
Centralized dependencies for the FastAPI application.
Following DRY principle - all dependencies in one place.
"""

from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.shared.database import SessionDep
from src.auth.service import AuthService, get_auth_service
from src.auth.models import User
from src.auth.utils import verify_token
from src.shared.utils import logger

# Security scheme
security = HTTPBearer()

# Custom header dependencies
async def get_token_header(x_token: Annotated[str, Header()]):
    """Validate X-Token header for admin operations."""
    if x_token != "fake-super-secret-token":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="X-Token header invalid"
        )

async def get_query_token(token: str):
    """Validate query token for API access."""
    if token != "jessica":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="No Jessica token provided"
        )

# Authentication dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user from JWT token."""
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id = int(payload.get("sub"))
        
        # Get user from database
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials, auth_service)
    except HTTPException:
        return None

# Permission decorators
def require_auth(func):
    """Decorator to require authentication."""
    func.__requires_auth__ = True
    return func

def require_superuser(func):
    """Decorator to require superuser permissions."""
    func.__requires_superuser__ = True
    return func

def require_active_user(func):
    """Decorator to require active user."""
    func.__requires_active_user__ = True
    return func

# Export all dependencies
__all__ = [
    "security",
    "get_token_header", 
    "get_query_token",
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser", 
    "get_optional_current_user",
    "require_auth",
    "require_superuser", 
    "require_active_user",
    "SessionDep"
]

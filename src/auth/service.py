"""
Authentication service following Service Layer pattern.
Uses Repository pattern for data access (Dependency Injection).
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from src.auth.models import User, RefreshToken
from src.auth.schemas import UserCreate, UserLogin, TokenRefresh
from src.auth.utils import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, verify_token, generate_token_hash
)
from src.auth.exceptions import (
    UserNotFoundException, UsernameTakenException, EmailTakenException,
    InvalidCredentialsException, TokenExpiredException, TokenInvalidException
)
from src.auth.repository import IUserRepository, IRefreshTokenRepository, UserRepository, RefreshTokenRepository
from src.shared.utils import logger


class AuthService:
    """Authentication service following Service Layer pattern."""
    
    def __init__(self, user_repository: IUserRepository, token_repository: IRefreshTokenRepository):
        """Initialize auth service with repositories (Dependency Injection)."""
        self.user_repository = user_repository
        self.token_repository = token_repository
    
    # ========== USER MANAGEMENT METHODS ==========
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            # Business logic validation
            await self._validate_user_data(user_data)
            await self._check_user_exists(user_data.username, user_data.email)
            
            # Hash password
            hashed_password = get_password_hash(user_data.password)
            
            # Create user using repository
            user = await self.user_repository.create_user(user_data, hashed_password)
            logger.info(f"User created: {user.username}")
            return user
            
        except (UsernameTakenException, EmailTakenException):
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
    
    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        try:
            # Get user by username
            user = await self.user_repository.get_user_by_username(username)
            if not user:
                return None
            
            # Verify password
            if not verify_password(password, user.hashed_password):
                return None
            
            # Update last login
            await self.user_repository.update_user(
                user.id, 
                {"last_login": datetime.utcnow()}
            )
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            return await self.user_repository.get_user_by_id(user_id)
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            return await self.user_repository.get_user_by_username(username)
        except Exception as e:
            logger.error(f"Error getting user by username: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            return await self.user_repository.get_user_by_email(email)
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def update_user(self, user_id: int, update_data: dict) -> Optional[User]:
        """Update user data."""
        try:
            return await self.user_repository.update_user(user_id, update_data)
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return None
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        try:
            # Revoke all user tokens first
            await self.token_repository.revoke_all_user_tokens(user_id)
            
            # Delete user
            return await self.user_repository.delete_user(user_id)
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return False
    
    # ========== TOKEN MANAGEMENT METHODS ==========
    
    async def create_tokens(self, user: User) -> Dict[str, str]:
        """Create access and refresh tokens for user."""
        try:
            # Create access token
            access_token_data = {"sub": str(user.id), "username": user.username}
            access_token = create_access_token(access_token_data)
            
            # Create refresh token
            refresh_token_data = {"sub": str(user.id), "username": user.username}
            refresh_token = create_refresh_token(refresh_token_data)
            
            # Store refresh token in database
            token_hash = generate_token_hash(refresh_token)
            expires_at = datetime.utcnow() + timedelta(days=30)  # 30 days
            
            await self.token_repository.create_token(
                user.id, token_hash, expires_at
            )
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token
            }
            
        except Exception as e:
            logger.error(f"Error creating tokens: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create tokens"
            )
    
    async def verify_refresh_token(self, refresh_token: str) -> Optional[User]:
        """Verify refresh token and return user."""
        try:
            # Verify token signature and expiration
            payload = verify_token(refresh_token, "refresh")
            user_id = int(payload.get("sub"))
            
            # Check if token exists in database and is not revoked
            token_hash = generate_token_hash(refresh_token)
            token_record = await self.token_repository.get_token_by_hash(token_hash)
            
            if not token_record or token_record.is_revoked:
                return None
            
            # Get user
            user = await self.user_repository.get_user_by_id(user_id)
            return user
            
        except (TokenExpiredException, TokenInvalidException):
            return None
        except Exception as e:
            logger.error(f"Error verifying refresh token: {e}")
            return None
    
    async def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke refresh token."""
        try:
            token_hash = generate_token_hash(refresh_token)
            return await self.token_repository.revoke_token(token_hash)
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
            return False
    
    async def revoke_all_user_tokens(self, user_id: int) -> bool:
        """Revoke all tokens for a user."""
        try:
            return await self.token_repository.revoke_all_user_tokens(user_id)
        except Exception as e:
            logger.error(f"Error revoking all user tokens: {e}")
            return False
    
    # ========== PRIVATE HELPER METHODS ==========
    
    async def _validate_user_data(self, user_data: UserCreate) -> None:
        """Validate user data (business logic)."""
        if not user_data.username or not user_data.email or not user_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username, email, and password are required"
            )
    
    async def _check_user_exists(self, username: str, email: str) -> None:
        """Check if user already exists (business logic)."""
        existing_username = await self.user_repository.get_user_by_username(username)
        if existing_username:
            raise UsernameTakenException()
        
        existing_email = await self.user_repository.get_user_by_email(email)
        if existing_email:
            raise EmailTakenException()


# ========== DEPENDENCY INJECTION FUNCTIONS ==========

def get_user_repository(session) -> IUserRepository:
    """Get user repository instance."""
    return UserRepository(session)

def get_token_repository(session) -> IRefreshTokenRepository:
    """Get token repository instance."""
    return RefreshTokenRepository(session)

def get_auth_service(
    user_repo: IUserRepository = Depends(get_user_repository),
    token_repo: IRefreshTokenRepository = Depends(get_token_repository)
) -> AuthService:
    """Get auth service instance with dependency injection."""
    return AuthService(user_repo, token_repo)

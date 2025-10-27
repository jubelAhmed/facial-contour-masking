"""
Consolidated authentication module.
Contains models, schemas, constants, exceptions, and utilities.
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import secrets
import hashlib

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, validator
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from passlib.context import CryptContext
from jose import jwt

from src.core.models import Base
from src.core.config import AuthConfig

# ============================================================================
# CONSTANTS & ENUMS
# ============================================================================

class TokenType(str, Enum):
    """JWT token types."""
    ACCESS = "access"
    REFRESH = "refresh"

class UserRole(str, Enum):
    """User roles."""
    USER = "user"
    SUPERUSER = "superuser"

class AuthErrorCode(str, Enum):
    """Authentication error codes."""
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_INVALID = "TOKEN_INVALID"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_INACTIVE = "USER_INACTIVE"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    PASSWORD_TOO_WEAK = "PASSWORD_TOO_WEAK"
    USERNAME_TAKEN = "USERNAME_TAKEN"
    EMAIL_TAKEN = "EMAIL_TAKEN"

# ============================================================================
# DATABASE MODELS
# ============================================================================

class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None
        }

class RefreshToken(Base):
    """Refresh token model."""
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_revoked = Column(Boolean, default=False)

# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        is_valid, error = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error)
        return v
    
    @validator('username')
    def validate_username(cls, v):
        is_valid, error = validate_username(v)
        if not is_valid:
            raise ValueError(error)
        return v

class UserLogin(BaseModel):
    """User login schema."""
    username: str
    password: str

class UserUpdate(BaseModel):
    """User update schema."""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """User response schema."""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    """Token refresh schema."""
    refresh_token: str

class PasswordChange(BaseModel):
    """Password change schema."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        is_valid, error = validate_password_strength(v)
        if not is_valid:
            raise ValueError(error)
        return v

# ============================================================================
# EXCEPTIONS
# ============================================================================

class AuthException(HTTPException):
    """Base authentication exception."""
    
    def __init__(self, detail: str, error_code: AuthErrorCode):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "detail": detail,
                "error_code": error_code.value
            },
            headers={"WWW-Authenticate": "Bearer"}
        )

class InvalidCredentialsException(AuthException):
    """Raised when credentials are invalid."""
    
    def __init__(self):
        super().__init__(
            "Invalid username or password",
            AuthErrorCode.INVALID_CREDENTIALS
        )

class TokenExpiredException(AuthException):
    """Raised when token has expired."""
    
    def __init__(self):
        super().__init__(
            "Token has expired",
            AuthErrorCode.TOKEN_EXPIRED
        )

class TokenInvalidException(AuthException):
    """Raised when token is invalid."""
    
    def __init__(self):
        super().__init__(
            "Invalid token",
            AuthErrorCode.TOKEN_INVALID
        )

class UserNotFoundException(HTTPException):
    """Raised when user is not found."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "detail": "User not found",
                "error_code": AuthErrorCode.USER_NOT_FOUND.value
            }
        )

class UserInactiveException(AuthException):
    """Raised when user account is inactive."""
    
    def __init__(self):
        super().__init__(
            "User account is inactive",
            AuthErrorCode.USER_INACTIVE
        )

class InsufficientPermissionsException(HTTPException):
    """Raised when user lacks required permissions."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "detail": "Insufficient permissions",
                "error_code": AuthErrorCode.INSUFFICIENT_PERMISSIONS.value
            }
        )

class PasswordTooWeakException(HTTPException):
    """Raised when password doesn't meet requirements."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": detail,
                "error_code": AuthErrorCode.PASSWORD_TOO_WEAK.value
            }
        )

class UsernameTakenException(HTTPException):
    """Raised when username is already taken."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": "Username already taken",
                "error_code": AuthErrorCode.USERNAME_TAKEN.value
            }
        )

class EmailTakenException(HTTPException):
    """Raised when email is already taken."""
    
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "detail": "Email already taken",
                "error_code": AuthErrorCode.EMAIL_TAKEN.value
            }
        )

# ============================================================================
# UTILITIES
# ============================================================================

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Get auth config
auth_config = AuthConfig()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=auth_config.access_token_expire_minutes)
    
    to_encode.update({"exp": expire, "type": TokenType.ACCESS.value})
    encoded_jwt = jwt.encode(to_encode, auth_config.secret_key, algorithm=auth_config.algorithm)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=auth_config.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": TokenType.REFRESH.value})
    encoded_jwt = jwt.encode(to_encode, auth_config.secret_key, algorithm=auth_config.algorithm)
    return encoded_jwt

def verify_token(token: str, token_type: TokenType = TokenType.ACCESS) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, auth_config.secret_key, algorithms=[auth_config.algorithm])
        
        # Check token type
        if payload.get("type") != token_type.value:
            raise TokenInvalidException()
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            raise TokenExpiredException()
        
        return payload
        
    except jwt.JWTError:
        raise TokenInvalidException()

def generate_token_hash(token: str) -> str:
    """Generate a hash for storing refresh tokens."""
    return hashlib.sha256(token.encode()).hexdigest()

def generate_random_string(length: int = 32) -> str:
    """Generate a random string for various purposes."""
    return secrets.token_urlsafe(length)

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Validate password strength and return (is_valid, error_message)."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    return True, ""

def validate_username(username: str) -> tuple[bool, str]:
    """Validate username format and return (is_valid, error_message)."""
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must be less than 50 characters"
    
    if not username.isalnum():
        return False, "Username must contain only alphanumeric characters"
    
    return True, ""

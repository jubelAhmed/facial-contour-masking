"""
Authentication repository following DAO pattern.
Implements data access operations for User entity.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import RefreshToken, User
from src.auth.schemas import UserCreate
from src.shared.utils import logger


class IUserRepository(ABC):
    """Interface for User repository operations."""

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass

    @abstractmethod
    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """Create new user."""
        pass

    @abstractmethod
    async def update_user(self, user_id: int, update_data: dict) -> Optional[User]:
        """Update user data."""
        pass

    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        pass

    @abstractmethod
    async def get_all_users(self) -> List[User]:
        """Get all users."""
        pass


class UserRepository(IUserRepository):
    """Concrete implementation of User repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        try:
            result = await self.session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        try:
            result = await self.session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        try:
            result = await self.session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            return None

    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """Create new user."""
        try:
            user = User(
                username=user_data.username,
                email=user_data.email,
                hashed_password=hashed_password,
            )
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            logger.info(f"User created: {user.username}")
            return user
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating user: {e}")
            raise

    async def update_user(self, user_id: int, update_data: dict) -> Optional[User]:
        """Update user data."""
        try:
            await self.session.execute(
                update(User).where(User.id == user_id).values(**update_data)
            )
            await self.session.commit()

            # Return updated user
            return await self.get_user_by_id(user_id)
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            return None

    async def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        try:
            await self.session.execute(delete(User).where(User.id == user_id))
            await self.session.commit()
            logger.info(f"User {user_id} deleted")
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting user {user_id}: {e}")
            return False

    async def get_all_users(self) -> List[User]:
        """Get all users."""
        try:
            result = await self.session.execute(select(User))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []


class IRefreshTokenRepository(ABC):
    """Interface for RefreshToken repository operations."""

    @abstractmethod
    async def create_token(
        self, user_id: int, token_hash: str, expires_at
    ) -> RefreshToken:
        """Create refresh token."""
        pass

    @abstractmethod
    async def get_token_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get token by hash."""
        pass

    @abstractmethod
    async def revoke_token(self, token_hash: str) -> bool:
        """Revoke token."""
        pass

    @abstractmethod
    async def revoke_all_user_tokens(self, user_id: int) -> bool:
        """Revoke all user tokens."""
        pass

    @abstractmethod
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens."""
        pass


class RefreshTokenRepository(IRefreshTokenRepository):
    """Concrete implementation of RefreshToken repository."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_token(
        self, user_id: int, token_hash: str, expires_at
    ) -> RefreshToken:
        """Create refresh token."""
        try:
            token = RefreshToken(
                user_id=user_id, token_hash=token_hash, expires_at=expires_at
            )
            self.session.add(token)
            await self.session.commit()
            await self.session.refresh(token)
            return token
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating refresh token: {e}")
            raise

    async def get_token_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Get token by hash."""
        try:
            result = await self.session.execute(
                select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting token by hash: {e}")
            return None

    async def revoke_token(self, token_hash: str) -> bool:
        """Revoke token."""
        try:
            await self.session.execute(
                update(RefreshToken)
                .where(RefreshToken.token_hash == token_hash)
                .values(is_revoked=True)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error revoking token: {e}")
            return False

    async def revoke_all_user_tokens(self, user_id: int) -> bool:
        """Revoke all user tokens."""
        try:
            await self.session.execute(
                update(RefreshToken)
                .where(RefreshToken.user_id == user_id)
                .values(is_revoked=True)
            )
            await self.session.commit()
            return True
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error revoking all user tokens: {e}")
            return False

    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens."""
        try:
            result = await self.session.execute(
                delete(RefreshToken).where(RefreshToken.expires_at < datetime.utcnow())
            )
            await self.session.commit()
            return result.rowcount
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0

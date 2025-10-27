"""
Test database configuration and utilities.
"""

import asyncio
import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from src.shared.models import Base
from src.shared.database import DatabaseManager


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create a test database engine."""
    # Use in-memory SQLite for testing
    database_url = "sqlite+aiosqlite:///:memory:"

    engine = create_async_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_db_manager(test_engine):
    """Create a test database manager."""
    manager = DatabaseManager()
    manager.engine = test_engine
    manager.session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    return manager


@pytest.fixture(autouse=True)
async def cleanup_database(test_engine):
    """Clean up database after each test."""
    yield

    # Clean up all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

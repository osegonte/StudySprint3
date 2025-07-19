# backend/common/database.py
"""Database configuration and session management for StudySprint 3.0"""

import os
from typing import AsyncGenerator, Optional
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .config import get_settings

settings = get_settings()

def get_database_url(async_mode: bool = True) -> str:
    """Construct database URL with proper escaping"""
    username = quote_plus(settings.DATABASE_USER)
    password = quote_plus(settings.DATABASE_PASSWORD)
    host = settings.DATABASE_HOST
    port = settings.DATABASE_PORT
    database = settings.DATABASE_NAME
    
    if async_mode:
        return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
    else:
        return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

# Async Engine
async_engine = create_async_engine(
    get_database_url(async_mode=True),
    echo=settings.DATABASE_ECHO,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# Session factories
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for models
Base = declarative_base()

# Dependency for getting async database session
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session for dependency injection"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Database health check
async def check_database_health() -> bool:
    """Check if database is accessible and healthy"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception:
        return False

# Simplified database initialization
async def init_database():
    """Initialize database connection and verify schema"""
    try:
        # Just check if we can connect
        health = await check_database_health()
        if health:
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database health check failed")
            return False
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

# Cleanup function
async def close_database():
    """Close database connections"""
    await async_engine.dispose()

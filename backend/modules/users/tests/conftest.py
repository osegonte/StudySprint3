
# backend/modules/users/tests/conftest.py
"""Fixed test configuration with proper async handling"""

import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient

from common.database import Base, get_async_db
from common.config import get_settings
from main import app
from modules.users.models import User, UserSession, UserPreferences
from modules.users.services import UserService, AuthService
from modules.users.schemas import UserCreate

# Get settings
settings = get_settings()

# Use a test database (same PostgreSQL instance, different database)
TEST_DATABASE_URL = f"postgresql+asyncpg://{settings.DATABASE_USER}:{settings.DATABASE_PASSWORD}@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/studysprint3_test"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_test_database():
    """Create test database schema"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_test_database) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session"""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()  # Rollback any changes after each test


@pytest.fixture
def client(db_session: AsyncSession) -> TestClient:
    """Create test client with database override"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_async_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def user_service(db_session: AsyncSession) -> UserService:
    """Create user service instance"""
    return UserService(db_session)


@pytest.fixture  
def auth_service(db_session: AsyncSession) -> AuthService:
    """Create auth service instance"""
    return AuthService(db_session)


@pytest.fixture
def sample_user_data() -> UserCreate:
    """Sample user data for testing"""
    unique_id = uuid4().hex[:8]
    return UserCreate(
        email=f"test{unique_id}@example.com",
        username=f"testuser{unique_id}",
        full_name="Test User",
        password="TestPassword123!",
        confirm_password="TestPassword123!"
    )


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, user_service: UserService, sample_user_data: UserCreate) -> User:
    """Create a test user in the database"""
    user = await user_service.create_user(sample_user_data)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def authenticated_user_tokens(
    db_session: AsyncSession, 
    auth_service: AuthService, 
    test_user: User
) -> tuple[str, str]:
    """Create authenticated user with tokens"""
    access_token, refresh_token, session = await auth_service.create_user_session(
        user=test_user,
        device_info="Test Device",
        ip_address="127.0.0.1",
        user_agent="Test Agent"
    )
    await db_session.commit()
    return access_token, refresh_token


@pytest.fixture
def auth_headers(authenticated_user_tokens: tuple[str, str]) -> dict:
    """Create authorization headers for authenticated requests"""
    access_token, _ = authenticated_user_tokens
    return {"Authorization": f"Bearer {access_token}"}


# Test data factories
def create_user_data(**kwargs) -> UserCreate:
    """Create user data with optional overrides"""
    unique_id = uuid4().hex[:8]
    defaults = {
        "email": f"user{unique_id}@example.com",
        "username": f"user{unique_id}",
        "full_name": "Test User",
        "password": "TestPassword123!",
        "confirm_password": "TestPassword123!"
    }
    defaults.update(kwargs)
    return UserCreate(**defaults)
# backend/modules/users/tests/test_services.py
"""Tests for user services"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from common.errors import (
    DuplicateResourceError, InvalidCredentialsError, AuthenticationError,
    ResourceNotFoundError, TokenExpiredError, InvalidTokenError
)
from modules.users.models import User, UserSession, UserPreferences
from modules.users.schemas import UserCreate, UserLogin, PasswordChange, UserUpdate
from modules.users.services import UserService, AuthService


class TestAuthService:
    """Test AuthService"""
    
    def test_password_hashing(self, auth_service):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        
        # Hash password
        hashed = auth_service.get_password_hash(password)
        
        # Verify correct password
        assert auth_service.verify_password(password, hashed) is True
        
        # Verify incorrect password
        assert auth_service.verify_password("WrongPassword", hashed) is False
    
    @pytest.mark.asyncio
    async def test_create_access_token(self, auth_service, test_user):
        """Test access token creation"""
        token = auth_service.create_access_token(test_user)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        token_data = auth_service.verify_token(token, "access")
        assert token_data.sub == str(test_user.id)
        assert token_data.email == test_user.email
        assert token_data.type == "access"
    
    @pytest.mark.asyncio
    async def test_create_refresh_token(self, auth_service, test_user):
        """Test refresh token creation"""
        token = auth_service.create_refresh_token(test_user)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify token
        token_data = auth_service.verify_token(token, "refresh")
        assert token_data.sub == str(test_user.id)
        assert token_data.type == "refresh"
    
    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, auth_service):
        """Test verification of invalid token"""
        with pytest.raises(InvalidTokenError):
            auth_service.verify_token("invalid_token")
    
    @pytest.mark.asyncio
    async def test_verify_expired_token(self, auth_service, test_user):
        """Test verification of expired token"""
        # Create token with negative expiration
        expired_token = auth_service.create_access_token(
            test_user, 
            expires_delta=timedelta(seconds=-1)
        )
        
        with pytest.raises(TokenExpiredError):
            auth_service.verify_token(expired_token)
    
    @pytest.mark.asyncio
    async def test_create_user_session(self, auth_service, test_user, db_session):
        """Test user session creation"""
        access_token, refresh_token, session = await auth_service.create_user_session(
            user=test_user,
            device_info="Test Device",
            ip_address="127.0.0.1",
            user_agent="Test Agent"
        )
        
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert isinstance(session, UserSession)
        assert session.user_id == test_user.id
        assert session.is_active is True
        assert session.device_info == "Test Device"
        assert session.ip_address == "127.0.0.1"
    
    @pytest.mark.asyncio
    async def test_refresh_access_token(self, auth_service, test_user, db_session):
        """Test access token refresh"""
        # Create initial session
        _, refresh_token, _ = await auth_service.create_user_session(test_user)
        
        # Refresh token
        new_access_token, new_refresh_token = await auth_service.refresh_access_token(refresh_token)
        
        assert isinstance(new_access_token, str)
        assert isinstance(new_refresh_token, str)
        assert new_access_token != refresh_token
    
    @pytest.mark.asyncio
    async def test_revoke_session(self, auth_service, test_user, db_session):
        """Test session revocation"""
        access_token, _, session = await auth_service.create_user_session(test_user)
        
        # Revoke session
        success = await auth_service.revoke_session(access_token, test_user.id)
        
        assert success is True
        
        # Refresh session from database
        await db_session.refresh(session)
        assert session.is_active is False
        assert session.revoked_at is not None


class TestUserService:
    """Test UserService"""
    
    @pytest.mark.asyncio
    async def test_create_user(self, user_service, sample_user_data):
        """Test user creation"""
        user = await user_service.create_user(sample_user_data)
        
        assert isinstance(user, User)
        assert user.email == sample_user_data.email.lower()
        assert user.username == sample_user_data.username.lower()
        assert user.full_name == sample_user_data.full_name
        assert user.is_active is True
        assert user.is_verified is False
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_service, sample_user_data, test_user):
        """Test creating user with duplicate email"""
        duplicate_data = sample_user_data.model_copy()
        duplicate_data.email = test_user.email
        duplicate_data.username = "different_username"
        
        with pytest.raises(DuplicateResourceError):
            await user_service.create_user(duplicate_data)
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_username(self, user_service, sample_user_data, test_user):
        """Test creating user with duplicate username"""
        duplicate_data = sample_user_data.model_copy()
        duplicate_data.email = "different@example.com"
        duplicate_data.username = test_user.username
        
        with pytest.raises(DuplicateResourceError):
            await user_service.create_user(duplicate_data)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, user_service, test_user):
        """Test successful user authentication"""
        login_data = UserLogin(
            email_or_username=test_user.email,
            password="TestPassword123!"
        )
        
        authenticated_user = await user_service.authenticate_user(login_data)
        
        assert authenticated_user.id == test_user.id
        assert authenticated_user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_authenticate_user_with_username(self, user_service, test_user):
        """Test user authentication with username"""
        login_data = UserLogin(
            email_or_username=test_user.username,
            password="TestPassword123!"
        )
        
        authenticated_user = await user_service.authenticate_user(login_data)
        
        assert authenticated_user.id == test_user.id
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, user_service, test_user):
        """Test authentication with wrong password"""
        login_data = UserLogin(
            email_or_username=test_user.email,
            password="WrongPassword123!"
        )
        
        with pytest.raises(InvalidCredentialsError):
            await user_service.authenticate_user(login_data)
    
    @pytest.mark.asyncio
    async def test_authenticate_nonexistent_user(self, user_service):
        """Test authentication of nonexistent user"""
        login_data = UserLogin(
            email_or_username="nonexistent@example.com",
            password="Password123!"
        )
        
        with pytest.raises(InvalidCredentialsError):
            await user_service.authenticate_user(login_data)
    
    @pytest.mark.asyncio
    async def test_update_user(self, user_service, test_user):
        """Test user update"""
        update_data = UserUpdate(
            full_name="Updated Name",
            email="updated@example.com"
        )
        
        updated_user = await user_service.update_user(test_user.id, update_data)
        
        assert updated_user.full_name == "Updated Name"
        assert updated_user.email == "updated@example.com"
    
    @pytest.mark.asyncio
    async def test_change_password(self, user_service, test_user):
        """Test password change"""
        password_data = PasswordChange(
            current_password="TestPassword123!",
            new_password="NewPassword123!",
            confirm_new_password="NewPassword123!"
        )
        
        success = await user_service.change_password(test_user.id, password_data)
        
        assert success is True
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, user_service, test_user):
        """Test password change with wrong current password"""
        password_data = PasswordChange(
            current_password="WrongPassword123!",
            new_password="NewPassword123!",
            confirm_new_password="NewPassword123!"
        )
        
        with pytest.raises(InvalidCredentialsError):
            await user_service.change_password(test_user.id, password_data)
    
    @pytest.mark.asyncio
    async def test_deactivate_user(self, user_service, test_user):
        """Test user deactivation"""
        success = await user_service.deactivate_user(
            test_user.id, 
            "TestPassword123!",
            "Test reason"
        )
        
        assert success is True


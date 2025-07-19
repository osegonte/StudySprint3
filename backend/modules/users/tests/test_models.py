# backend/modules/users/tests/test_models.py
"""Tests for user models"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from modules.users.models import User, UserSession, UserPreferences


class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self):
        """Test user model creation"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            full_name="Test User"
        )
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.subscription_tier == "free"
    
    def test_user_display_name_with_full_name(self):
        """Test display name when full name is provided"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            full_name="Test User"
        )
        
        assert user.display_name == "Test User"
    
    def test_user_display_name_without_full_name(self):
        """Test display name when full name is not provided"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password"
        )
        
        assert user.display_name == "testuser"
    
    def test_user_is_authenticated(self):
        """Test user authentication status"""
        active_user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            is_active=True
        )
        
        inactive_user = User(
            email="test2@example.com",
            username="testuser2",
            hashed_password="hashed_password",
            is_active=False
        )
        
        assert active_user.is_authenticated is True
        assert inactive_user.is_authenticated is False


class TestUserSessionModel:
    """Test UserSession model"""
    
    def test_session_creation(self):
        """Test session model creation"""
        user_id = uuid4()
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        session = UserSession(
            user_id=user_id,
            session_token="test_token",
            refresh_token="refresh_token",
            expires_at=expires_at,
            ip_address="127.0.0.1",
            user_agent="Test Agent"
        )
        
        assert session.user_id == user_id
        assert session.session_token == "test_token"
        assert session.refresh_token == "refresh_token"
        assert session.is_active is True
        assert session.ip_address == "127.0.0.1"
    
    def test_session_is_expired(self):
        """Test session expiration check"""
        past_time = datetime.utcnow() - timedelta(hours=1)
        future_time = datetime.utcnow() + timedelta(hours=1)
        
        expired_session = UserSession(
            user_id=uuid4(),
            session_token="token",
            expires_at=past_time
        )
        
        valid_session = UserSession(
            user_id=uuid4(),
            session_token="token",
            expires_at=future_time
        )
        
        assert expired_session.is_expired is True
        assert valid_session.is_expired is False
    
    def test_session_is_valid(self):
        """Test session validity check"""
        future_time = datetime.utcnow() + timedelta(hours=1)
        past_time = datetime.utcnow() - timedelta(hours=1)
        
        # Valid session
        valid_session = UserSession(
            user_id=uuid4(),
            session_token="token",
            expires_at=future_time,
            is_active=True
        )
        
        # Expired session
        expired_session = UserSession(
            user_id=uuid4(),
            session_token="token",
            expires_at=past_time,
            is_active=True
        )
        
        # Revoked session
        revoked_session = UserSession(
            user_id=uuid4(),
            session_token="token",
            expires_at=future_time,
            is_active=False
        )
        
        assert valid_session.is_valid is True
        assert expired_session.is_valid is False
        assert revoked_session.is_valid is False


class TestUserPreferencesModel:
    """Test UserPreferences model"""
    
    def test_preferences_creation(self):
        """Test preferences model creation"""
        user_id = uuid4()
        
        preferences = UserPreferences(user_id=user_id)
        
        assert preferences.user_id == user_id
        assert preferences.theme == "light"
        assert preferences.language == "en"
        assert preferences.timezone == "UTC"
        assert preferences.default_study_duration == 25
        assert preferences.default_break_duration == 5
    
    def test_get_notification_setting(self):
        """Test getting notification settings"""
        preferences = UserPreferences(
            user_id=uuid4(),
            notification_settings={
                "email_notifications": True,
                "study_reminders": False
            }
        )
        
        assert preferences.get_notification_setting("email_notifications") is True
        assert preferences.get_notification_setting("study_reminders") is False
        assert preferences.get_notification_setting("nonexistent") is False
    
    def test_get_study_preference(self):
        """Test getting study preferences"""
        preferences = UserPreferences(
            user_id=uuid4(),
            study_preferences={
                "reading_speed_tracking": True,
                "idle_detection_threshold": 30
            }
        )
        
        assert preferences.get_study_preference("reading_speed_tracking") is True
        assert preferences.get_study_preference("idle_detection_threshold") == 30
        assert preferences.get_study_preference("nonexistent") is None

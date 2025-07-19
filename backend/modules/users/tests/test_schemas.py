# backend/modules/users/tests/test_schemas.py
"""Tests for user schemas"""

import pytest
from pydantic import ValidationError

from modules.users.schemas import (
    UserCreate, UserUpdate, UserLogin, PasswordChange,
    UserPreferencesUpdate
)


class TestUserCreateSchema:
    """Test UserCreate schema validation"""
    
    def test_valid_user_creation(self):
        """Test valid user creation data"""
        data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "password": "TestPassword123!",
            "confirm_password": "TestPassword123!"
        }
        
        user = UserCreate(**data)
        
        assert user.email == "test@example.com"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
    
    def test_username_validation(self):
        """Test username validation rules"""
        base_data = {
            "email": "test@example.com",
            "password": "TestPassword123!",
            "confirm_password": "TestPassword123!"
        }
        
        # Valid username
        user = UserCreate(username="valid_user123", **base_data)
        assert user.username == "valid_user123"
        
        # Username too short
        with pytest.raises(ValidationError):
            UserCreate(username="ab", **base_data)
        
        # Username too long
        with pytest.raises(ValidationError):
            UserCreate(username="a" * 31, **base_data)
        
        # Invalid characters
        with pytest.raises(ValidationError):
            UserCreate(username="user@name", **base_data)
    
    def test_password_validation(self):
        """Test password validation rules"""
        base_data = {
            "email": "test@example.com",
            "username": "testuser",
            "confirm_password": "TestPassword123!"
        }
        
        # Valid password
        user = UserCreate(password="TestPassword123!", **base_data)
        assert user.password == "TestPassword123!"
        
        # Password too short
        with pytest.raises(ValidationError):
            UserCreate(password="Short1!", confirm_password="Short1!", **base_data)
        
        # No uppercase
        with pytest.raises(ValidationError):
            UserCreate(password="testpassword123!", confirm_password="testpassword123!", **base_data)
        
        # No lowercase
        with pytest.raises(ValidationError):
            UserCreate(password="TESTPASSWORD123!", confirm_password="TESTPASSWORD123!", **base_data)
        
        # No digits
        with pytest.raises(ValidationError):
            UserCreate(password="TestPassword!", confirm_password="TestPassword!", **base_data)
        
        # No special characters
        with pytest.raises(ValidationError):
            UserCreate(password="TestPassword123", confirm_password="TestPassword123", **base_data)
    
    def test_password_confirmation(self):
        """Test password confirmation validation"""
        base_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPassword123!"
        }
        
        # Matching passwords
        user = UserCreate(confirm_password="TestPassword123!", **base_data)
        assert user.confirm_password == "TestPassword123!"
        
        # Non-matching passwords
        with pytest.raises(ValidationError):
            UserCreate(confirm_password="DifferentPassword123!", **base_data)


class TestUserUpdateSchema:
    """Test UserUpdate schema validation"""
    
    def test_valid_user_update(self):
        """Test valid user update data"""
        data = {
            "email": "updated@example.com",
            "username": "updateduser",
            "full_name": "Updated User"
        }
        
        update = UserUpdate(**data)
        
        assert update.email == "updated@example.com"
        assert update.username == "updateduser"
        assert update.full_name == "Updated User"
    
    def test_partial_update(self):
        """Test partial user update"""
        update = UserUpdate(full_name="New Name")
        
        assert update.full_name == "New Name"
        assert update.email is None
        assert update.username is None


class TestUserLoginSchema:
    """Test UserLogin schema validation"""
    
    def test_valid_login(self):
        """Test valid login data"""
        data = {
            "email_or_username": "test@example.com",
            "password": "password123"
        }
        
        login = UserLogin(**data)
        
        assert login.email_or_username == "test@example.com"
        assert login.password == "password123"
        assert login.remember_me is False
    
    def test_login_with_remember_me(self):
        """Test login with remember me option"""
        data = {
            "email_or_username": "testuser",
            "password": "password123",
            "remember_me": True
        }
        
        login = UserLogin(**data)
        
        assert login.remember_me is True


class TestPasswordChangeSchema:
    """Test PasswordChange schema validation"""
    
    def test_valid_password_change(self):
        """Test valid password change data"""
        data = {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "confirm_new_password": "NewPassword123!"
        }
        
        change = PasswordChange(**data)
        
        assert change.current_password == "OldPassword123!"
        assert change.new_password == "NewPassword123!"
        assert change.confirm_new_password == "NewPassword123!"
    
    def test_password_confirmation_mismatch(self):
        """Test password confirmation mismatch"""
        data = {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "confirm_new_password": "DifferentPassword123!"
        }
        
        with pytest.raises(ValidationError):
            PasswordChange(**data)


class TestUserPreferencesUpdateSchema:
    """Test UserPreferencesUpdate schema validation"""
    
    def test_valid_preferences_update(self):
        """Test valid preferences update"""
        data = {
            "theme": "dark",
            "language": "en",
            "default_study_duration": 30,
            "daily_study_goal_minutes": 180
        }
        
        preferences = UserPreferencesUpdate(**data)
        
        assert preferences.theme == "dark"
        assert preferences.language == "en"
        assert preferences.default_study_duration == 30
        assert preferences.daily_study_goal_minutes == 180
    
    def test_invalid_theme(self):
        """Test invalid theme validation"""
        with pytest.raises(ValidationError):
            UserPreferencesUpdate(theme="invalid_theme")
    
    def test_invalid_study_duration(self):
        """Test invalid study duration validation"""
        # Too short
        with pytest.raises(ValidationError):
            UserPreferencesUpdate(default_study_duration=1)
        
        # Too long
        with pytest.raises(ValidationError):
            UserPreferencesUpdate(default_study_duration=200)
    
    def test_invalid_language(self):
        """Test invalid language code validation"""
        with pytest.raises(ValidationError):
            UserPreferencesUpdate(language="invalid")
    
    def test_partial_preferences_update(self):
        """Test partial preferences update"""
        preferences = UserPreferencesUpdate(theme="dark")
        
        assert preferences.theme == "dark"
        assert preferences.language is None
        assert preferences.default_study_duration is None

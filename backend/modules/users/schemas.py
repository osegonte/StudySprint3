# backend/modules/users/schemas.py
"""Pydantic schemas for user module"""

from datetime import datetime
from typing import Dict, Optional, Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
import re


# Base schemas
class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not v:
            raise ValueError('Username cannot be empty')
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 30:
            raise ValueError('Username must be 30 characters or less')
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
        return v.lower()
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate full name format"""
        if v is not None:
            v = v.strip()
            if len(v) > 255:
                raise ValueError('Full name must be 255 characters or less')
            if len(v) == 0:
                return None
        return v


# User creation schemas
class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str
    confirm_password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be 128 characters or less')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that passwords match"""
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        """Validate username format"""
        if v is not None:
            if len(v) < 3:
                raise ValueError('Username must be at least 3 characters long')
            if len(v) > 30:
                raise ValueError('Username must be 30 characters or less')
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Username can only contain letters, numbers, underscores, and hyphens')
            return v.lower()
        return v


# Authentication schemas
class UserLogin(BaseModel):
    """Schema for user login"""
    email_or_username: str
    password: str
    remember_me: bool = False
    
    @field_validator('email_or_username')
    @classmethod
    def validate_email_or_username(cls, v: str) -> str:
        """Validate email or username format"""
        if not v:
            raise ValueError('Email or username cannot be empty')
        return v.strip().lower()


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str
    confirm_new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be 128 characters or less')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @field_validator('confirm_new_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that new passwords match"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('New passwords do not match')
        return v


class PasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""
    token: str
    new_password: str
    confirm_new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        # Add other password validation rules here
        return v
    
    @field_validator('confirm_new_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that passwords match"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


# Token schemas
class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires
    refresh_expires_in: int  # seconds until refresh token expires


class TokenRefresh(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str


class TokenData(BaseModel):
    """Schema for token payload data"""
    sub: str  # user ID
    email: str
    username: str
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    jti: str  # JWT ID
    type: str  # token type (access or refresh)


# User response schemas
class UserResponse(BaseModel):
    """Schema for user response data"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    subscription_tier: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None


class UserProfile(UserResponse):
    """Extended user profile schema"""
    # Add any additional fields that should be included in profile view
    pass


class UserPublic(BaseModel):
    """Public user information (for sharing/mentions)"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    username: str
    full_name: Optional[str] = None


# User preferences schemas
class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences"""
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    default_study_duration: Optional[int] = None
    default_break_duration: Optional[int] = None
    auto_start_timer: Optional[bool] = None
    daily_study_goal_minutes: Optional[int] = None
    notification_settings: Optional[Dict[str, Any]] = None
    study_preferences: Optional[Dict[str, Any]] = None
    privacy_settings: Optional[Dict[str, Any]] = None
    
    @field_validator('theme')
    @classmethod
    def validate_theme(cls, v: Optional[str]) -> Optional[str]:
        """Validate theme option"""
        if v is not None:
            valid_themes = ['light', 'dark', 'auto']
            if v not in valid_themes:
                raise ValueError(f'Theme must be one of: {", ".join(valid_themes)}')
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """Validate language code"""
        if v is not None:
            # Basic validation for ISO language codes
            if not re.match(r'^[a-z]{2}(-[A-Z]{2})?$', v):
                raise ValueError('Language must be a valid ISO language code (e.g., en, en-US)')
        return v
    
    @field_validator('default_study_duration')
    @classmethod
    def validate_study_duration(cls, v: Optional[int]) -> Optional[int]:
        """Validate study duration"""
        if v is not None:
            if v < 5 or v > 180:
                raise ValueError('Study duration must be between 5 and 180 minutes')
        return v
    
    @field_validator('default_break_duration')
    @classmethod
    def validate_break_duration(cls, v: Optional[int]) -> Optional[int]:
        """Validate break duration"""
        if v is not None:
            if v < 1 or v > 60:
                raise ValueError('Break duration must be between 1 and 60 minutes')
        return v
    
    @field_validator('daily_study_goal_minutes')
    @classmethod
    def validate_daily_goal(cls, v: Optional[int]) -> Optional[int]:
        """Validate daily study goal"""
        if v is not None:
            if v < 15 or v > 720:  # 15 minutes to 12 hours
                raise ValueError('Daily study goal must be between 15 and 720 minutes')
        return v


class UserPreferencesResponse(BaseModel):
    """Schema for user preferences response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    theme: str
    language: str
    timezone: str
    default_study_duration: int
    default_break_duration: int
    auto_start_timer: bool
    daily_study_goal_minutes: int
    notification_settings: Dict[str, Any]
    study_preferences: Dict[str, Any]
    privacy_settings: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# Session management schemas
class UserSessionResponse(BaseModel):
    """Schema for user session response"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    is_active: bool


class LogoutRequest(BaseModel):
    """Schema for logout request"""
    logout_all_devices: bool = False


# API response schemas
class ApiResponse(BaseModel):
    """Generic API response schema"""
    success: bool
    message: str
    data: Optional[Any] = None


class UserApiResponse(ApiResponse):
    """User-specific API response schema"""
    data: Optional[UserResponse] = None


class AuthResponse(ApiResponse):
    """Authentication response schema"""
    data: Optional[Dict[str, Any]] = None  # Contains user and token data


# Email verification schemas
class EmailVerificationRequest(BaseModel):
    """Schema for email verification request"""
    email: EmailStr


class EmailVerificationConfirm(BaseModel):
    """Schema for confirming email verification"""
    token: str


# Account management schemas
class AccountDeactivation(BaseModel):
    """Schema for account deactivation"""
    password: str
    reason: Optional[str] = None
    
    @field_validator('reason')
    @classmethod
    def validate_reason(cls, v: Optional[str]) -> Optional[str]:
        """Validate deactivation reason"""
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('Reason must be 500 characters or less')
        return v
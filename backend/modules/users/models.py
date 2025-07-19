# backend/modules/users/models.py (Updated with Topics relationship)
"""User models for StudySprint 3.0 - Updated with Topics relationship"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from common.database import Base


class User(Base):
    """User model with complete profile and authentication fields"""
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    
    # Profile fields
    full_name = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False, server_default='true')
    is_verified = Column(Boolean, default=False, nullable=False, server_default='false')
    is_superuser = Column(Boolean, default=False, nullable=False, server_default='false')
    
    # Subscription
    subscription_tier = Column(String(20), default='free', nullable=False, server_default='free')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Email verification
    email_verification_token = Column(String(255), nullable=True)
    email_verification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    # Topics relationship - Added
    topics = relationship("Topic", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
    
    @property
    def is_authenticated(self) -> bool:
        """Check if user is authenticated (active and verified for now)"""
        return self.is_active
    
    @property
    def display_name(self) -> str:
        """Get display name (full name or username)"""
        return self.full_name if self.full_name else self.username


class UserSession(Base):
    """User session model for JWT token management"""
    __tablename__ = "user_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Session details
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    
    # Session metadata
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)  # Support IPv6
    user_agent = Column(Text, nullable=True)
    
    # Session timing
    expires_at = Column(DateTime(timezone=True), nullable=False)
    refresh_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False, server_default='true')
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revocation_reason = Column(String(100), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Check if session is valid (active and not expired)"""
        return self.is_active and not self.is_expired and self.revoked_at is None


class UserPreferences(Base):
    """User preferences and settings"""
    __tablename__ = "user_preferences"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign key to user (one-to-one relationship)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # UI Preferences
    theme = Column(String(20), default='light', nullable=False, server_default='light')
    language = Column(String(10), default='en', nullable=False, server_default='en')
    timezone = Column(String(50), default='UTC', nullable=False, server_default='UTC')
    
    # Study Preferences
    default_study_duration = Column(Integer, default=25, nullable=False, server_default='25')
    default_break_duration = Column(Integer, default=5, nullable=False, server_default='5')
    auto_start_timer = Column(Boolean, default=False, nullable=False, server_default='false')
    daily_study_goal_minutes = Column(Integer, default=120, nullable=False, server_default='120')
    
    # Notification Preferences (JSON structure)
    notification_settings = Column(JSONB, default={
        "email_notifications": True,
        "study_reminders": True,
        "goal_achievements": True,
        "weekly_reports": True,
        "break_reminders": True,
        "session_summaries": True
    }, nullable=False, server_default='{}')
    
    # Advanced Study Settings (JSON structure)
    study_preferences = Column(JSONB, default={
        "reading_speed_tracking": True,
        "page_time_tracking": True,
        "idle_detection_threshold": 30,
        "auto_save_notes": True,
        "smart_highlights": True,
        "exercise_suggestions": True
    }, nullable=False, server_default='{}')
    
    # Privacy Settings (JSON structure)
    privacy_settings = Column(JSONB, default={
        "profile_visibility": "private",
        "share_study_stats": False,
        "data_collection": True,
        "analytics_tracking": True
    }, nullable=False, server_default='{}')
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(id={self.id}, user_id={self.user_id}, theme={self.theme})>"
    
    def get_notification_setting(self, setting_name: str) -> bool:
        """Get specific notification setting"""
        return self.notification_settings.get(setting_name, False)
    
    def get_study_preference(self, preference_name: str):
        """Get specific study preference"""
        return self.study_preferences.get(preference_name)
    
    def get_privacy_setting(self, setting_name: str):
        """Get specific privacy setting"""
        return self.privacy_settings.get(setting_name)


# Migration helper functions
def create_default_preferences(user_id: UUID) -> UserPreferences:
    """Create default preferences for a new user"""
    return UserPreferences(user_id=user_id)
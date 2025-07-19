# backend/modules/users/services.py
"""User services for business logic and database operations"""

import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy import or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from common.config import get_settings
from common.errors import (
    AuthenticationError, InvalidCredentialsError, TokenExpiredError,
    InvalidTokenError, DuplicateResourceError, ResourceNotFoundError,
    ValidationError, BusinessLogicError
)
from .models import User, UserSession, UserPreferences
from .schemas import (
    UserCreate, UserUpdate, UserLogin, PasswordChange,
    UserPreferencesUpdate, TokenData
)

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"


class AuthService:
    """Authentication service for JWT and session management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(
        self, 
        user: User, 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Create token data
        to_encode = TokenData(
            sub=str(user.id),
            email=user.email,
            username=user.username,
            exp=int(expire.timestamp()),
            iat=int(datetime.utcnow().timestamp()),
            jti=secrets.token_urlsafe(32),  # JWT ID for tracking
            type="access"
        ).model_dump()
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    def create_refresh_token(
        self, 
        user: User,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode = TokenData(
            sub=str(user.id),
            email=user.email,
            username=user.username,
            exp=int(expire.timestamp()),
            iat=int(datetime.utcnow().timestamp()),
            jti=secrets.token_urlsafe(32),
            type="refresh"
        ).model_dump()
        
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_token(self, token: str, token_type: str = "access") -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            
            # Validate token type
            if payload.get("type") != token_type:
                raise InvalidTokenError(f"Invalid token type. Expected {token_type}")
            
            # Check expiration
            exp = payload.get("exp")
            if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
                raise TokenExpiredError()
            
            return TokenData(**payload)
            
        except JWTError as e:
            raise InvalidTokenError(f"Token validation failed: {str(e)}")
    
    async def create_user_session(
        self,
        user: User,
        device_info: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        remember_me: bool = False
    ) -> Tuple[str, str, UserSession]:
        """Create a new user session with tokens"""
        
        # Create tokens
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        if remember_me:
            # Extend refresh token for "remember me"
            refresh_token_expires = timedelta(days=30)
        
        access_token = self.create_access_token(user, access_token_expires)
        refresh_token = self.create_refresh_token(user, refresh_token_expires)
        
        # Create session record
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + access_token_expires,
            refresh_expires_at=datetime.utcnow() + refresh_token_expires,
            is_active=True
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        # Update user's last login
        user.last_login = datetime.utcnow()
        await self.db.commit()
        
        return access_token, refresh_token, session
    
    async def refresh_access_token(self, refresh_token: str) -> Tuple[str, str]:
        """Refresh access token using refresh token"""
        
        # Verify refresh token
        try:
            token_data = self.verify_token(refresh_token, "refresh")
        except (TokenExpiredError, InvalidTokenError) as e:
            raise AuthenticationError("Invalid or expired refresh token")
        
        # Get user
        user = await self.get_user_by_id(UUID(token_data.sub))
        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")
        
        # Find and validate session
        session_query = select(UserSession).where(
            and_(
                UserSession.refresh_token == refresh_token,
                UserSession.user_id == user.id,
                UserSession.is_active == True
            )
        )
        result = await self.db.execute(session_query)
        session = result.scalar_one_or_none()
        
        if not session or not session.is_valid:
            raise AuthenticationError("Invalid session")
        
        # Create new tokens
        new_access_token = self.create_access_token(user)
        new_refresh_token = self.create_refresh_token(user)
        
        # Update session
        session.session_token = new_access_token
        session.refresh_token = new_refresh_token
        session.expires_at = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        session.refresh_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        session.last_used_at = datetime.utcnow()
        
        await self.db.commit()
        
        return new_access_token, new_refresh_token
    
    async def revoke_session(self, session_token: str, user_id: UUID, revoke_all: bool = False) -> bool:
        """Revoke user session(s)"""
        
        if revoke_all:
            # Revoke all active sessions for the user
            sessions_query = select(UserSession).where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
            result = await self.db.execute(sessions_query)
            sessions = result.scalars().all()
            
            for session in sessions:
                session.is_active = False
                session.revoked_at = datetime.utcnow()
                session.revocation_reason = "logout_all"
            
            await self.db.commit()
            return len(sessions) > 0
        else:
            # Revoke specific session
            session_query = select(UserSession).where(
                and_(
                    UserSession.session_token == session_token,
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
            result = await self.db.execute(session_query)
            session = result.scalar_one_or_none()
            
            if session:
                session.is_active = False
                session.revoked_at = datetime.utcnow()
                session.revocation_reason = "logout"
                await self.db.commit()
                return True
            
            return False
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_current_user(self, token: str) -> User:
        """Get current user from token"""
        try:
            token_data = self.verify_token(token)
        except (TokenExpiredError, InvalidTokenError) as e:
            raise AuthenticationError("Invalid token")
        
        user = await self.get_user_by_id(UUID(token_data.sub))
        if not user:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is deactivated")
        
        return user


class UserService:
    """User service for user management operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.auth_service = AuthService(db)
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        
        # Check if email already exists
        email_query = select(User).where(User.email == user_data.email.lower())
        result = await self.db.execute(email_query)
        if result.scalar_one_or_none():
            raise DuplicateResourceError("User", "email")
        
        # Check if username already exists
        username_query = select(User).where(User.username == user_data.username.lower())
        result = await self.db.execute(username_query)
        if result.scalar_one_or_none():
            raise DuplicateResourceError("User", "username")
        
        # Hash password
        hashed_password = self.auth_service.get_password_hash(user_data.password)
        
        # Create user
        user = User(
            email=user_data.email.lower(),
            username=user_data.username.lower(),
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            is_active=True,
            is_verified=False,  # Will be verified via email
            subscription_tier='free'
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # Create default preferences
        preferences = UserPreferences(user_id=user.id)
        self.db.add(preferences)
        await self.db.commit()
        
        return user
    
    async def authenticate_user(self, login_data: UserLogin) -> User:
        """Authenticate user with email/username and password"""
        
        # Find user by email or username
        user_query = select(User).where(
            or_(
                User.email == login_data.email_or_username.lower(),
                User.username == login_data.email_or_username.lower()
            )
        )
        result = await self.db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise InvalidCredentialsError()
        
        # Verify password
        if not self.auth_service.verify_password(login_data.password, user.hashed_password):
            raise InvalidCredentialsError()
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationError("Account is deactivated")
        
        return user
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID with preferences"""
        query = select(User).options(selectinload(User.preferences)).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        query = select(User).where(User.email == email.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        query = select(User).where(User.username == username.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> User:
        """Update user information"""
        
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        # Check for email conflicts
        if user_data.email and user_data.email.lower() != user.email:
            email_query = select(User).where(User.email == user_data.email.lower())
            result = await self.db.execute(email_query)
            if result.scalar_one_or_none():
                raise DuplicateResourceError("User", "email")
            user.email = user_data.email.lower()
            user.is_verified = False  # Re-verify email
        
        # Check for username conflicts
        if user_data.username and user_data.username.lower() != user.username:
            username_query = select(User).where(User.username == user_data.username.lower())
            result = await self.db.execute(username_query)
            if result.scalar_one_or_none():
                raise DuplicateResourceError("User", "username")
            user.username = user_data.username.lower()
        
        # Update other fields
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        
        user.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def change_password(self, user_id: UUID, password_data: PasswordChange) -> bool:
        """Change user password"""
        
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        # Verify current password
        if not self.auth_service.verify_password(password_data.current_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Hash new password
        new_hashed_password = self.auth_service.get_password_hash(password_data.new_password)
        
        # Update password
        user.hashed_password = new_hashed_password
        user.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Revoke all existing sessions (force re-login)
        await self.auth_service.revoke_session("", user_id, revoke_all=True)
        
        return True
    
    async def deactivate_user(self, user_id: UUID, password: str, reason: Optional[str] = None) -> bool:
        """Deactivate user account"""
        
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        # Verify password
        if not self.auth_service.verify_password(password, user.hashed_password):
            raise InvalidCredentialsError("Password is incorrect")
        
        # Deactivate user
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Revoke all sessions
        await self.auth_service.revoke_session("", user_id, revoke_all=True)
        
        return True
    
    async def reactivate_user(self, user_id: UUID) -> bool:
        """Reactivate user account (admin function)"""
        
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", str(user_id))
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        await self.db.commit()
        
        return True
    
    async def get_user_sessions(self, user_id: UUID) -> List[UserSession]:
        """Get all active sessions for a user"""
        
        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        ).order_by(UserSession.last_used_at.desc())
        
        result = await self.db.execute(query)
        return result.scalars().all()


class UserPreferencesService:
    """Service for managing user preferences"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_preferences(self, user_id: UUID) -> Optional[UserPreferences]:
        """Get user preferences"""
        query = select(UserPreferences).where(UserPreferences.user_id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_user_preferences(
        self, 
        user_id: UUID, 
        preferences_data: UserPreferencesUpdate
    ) -> UserPreferences:
        """Update user preferences"""
        
        # Get existing preferences
        preferences = await self.get_user_preferences(user_id)
        if not preferences:
            # Create default preferences if they don't exist
            preferences = UserPreferences(user_id=user_id)
            self.db.add(preferences)
            await self.db.commit()
            await self.db.refresh(preferences)
        
        # Update fields
        update_data = preferences_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(preferences, field) and value is not None:
                if field in ['notification_settings', 'study_preferences', 'privacy_settings']:
                    # For JSON fields, merge with existing settings
                    current_settings = getattr(preferences, field) or {}
                    current_settings.update(value)
                    setattr(preferences, field, current_settings)
                else:
                    setattr(preferences, field, value)
        
        preferences.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(preferences)
        
        return preferences
    
    async def reset_user_preferences(self, user_id: UUID) -> UserPreferences:
        """Reset user preferences to defaults"""
        
        preferences = await self.get_user_preferences(user_id)
        if not preferences:
            raise ResourceNotFoundError("UserPreferences", str(user_id))
        
        # Reset to defaults
        preferences.theme = 'light'
        preferences.language = 'en'
        preferences.timezone = 'UTC'
        preferences.default_study_duration = 25
        preferences.default_break_duration = 5
        preferences.auto_start_timer = False
        preferences.daily_study_goal_minutes = 120
        preferences.notification_settings = {
            "email_notifications": True,
            "study_reminders": True,
            "goal_achievements": True,
            "weekly_reports": True,
            "break_reminders": True,
            "session_summaries": True
        }
        preferences.study_preferences = {
            "reading_speed_tracking": True,
            "page_time_tracking": True,
            "idle_detection_threshold": 30,
            "auto_save_notes": True,
            "smart_highlights": True,
            "exercise_suggestions": True
        }
        preferences.privacy_settings = {
            "profile_visibility": "private",
            "share_study_stats": False,
            "data_collection": True,
            "analytics_tracking": True
        }
        preferences.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(preferences)
        
        return preferences


# Utility functions
async def get_user_service(db: AsyncSession) -> UserService:
    """Get user service instance"""
    return UserService(db)


async def get_auth_service(db: AsyncSession) -> AuthService:
    """Get auth service instance"""
    return AuthService(db)


async def get_preferences_service(db: AsyncSession) -> UserPreferencesService:
    """Get preferences service instance"""
    return UserPreferencesService(db)
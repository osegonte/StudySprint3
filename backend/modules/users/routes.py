# backend/modules/users/routes.py
"""API routes for user module"""

from datetime import timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_async_db
from common.config import get_settings
from common.errors import (
    StudySprintException, AuthenticationError, InvalidCredentialsError,
    DuplicateResourceError, ResourceNotFoundError, ValidationError
)
from .models import User, UserSession, UserPreferences
from .schemas import (
    UserCreate, UserUpdate, UserLogin, PasswordChange, 
    UserResponse, UserProfile, Token, TokenRefresh, LogoutRequest,
    UserPreferencesUpdate, UserPreferencesResponse, UserSessionResponse,
    ApiResponse, UserApiResponse, AuthResponse
)
from .services import UserService, AuthService, UserPreferencesService

settings = get_settings()
router = APIRouter()
security = HTTPBearer()


# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> User:
    """Get current authenticated user"""
    try:
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except StudySprintException:
        raise
    except Exception as e:
        raise AuthenticationError("Authentication failed")


# Optional dependency for getting current user (doesn't raise on auth failure)
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise"""
    if not credentials:
        return None
    
    try:
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except:
        return None


def get_client_info(request: Request) -> dict:
    """Extract client information from request"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "device_info": request.headers.get("x-device-info")  # Custom header from frontend
    }


# Authentication endpoints
@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Register a new user"""
    try:
        user_service = UserService(db)
        auth_service = AuthService(db)
        
        # Create user
        user = await user_service.create_user(user_data)
        
        # Create session and tokens
        client_info = get_client_info(request)
        access_token, refresh_token, session = await auth_service.create_user_session(
            user=user,
            device_info=client_info.get("device_info"),
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
            remember_me=False
        )
        
        # Prepare response
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        }
        
        user_response = UserResponse.model_validate(user)
        
        return AuthResponse(
            success=True,
            message="User registered successfully",
            data={
                "user": user_response.model_dump(),
                "tokens": token_data
            }
        )
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=AuthResponse)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    """Login user and create session"""
    try:
        user_service = UserService(db)
        auth_service = AuthService(db)
        
        # Authenticate user
        user = await user_service.authenticate_user(login_data)
        
        # Create session and tokens
        client_info = get_client_info(request)
        access_token, refresh_token, session = await auth_service.create_user_session(
            user=user,
            device_info=client_info.get("device_info"),
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent"),
            remember_me=login_data.remember_me
        )
        
        # Prepare response
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": (30 if login_data.remember_me else settings.REFRESH_TOKEN_EXPIRE_DAYS) * 24 * 60 * 60
        }
        
        user_response = UserResponse.model_validate(user)
        
        return AuthResponse(
            success=True,
            message="Login successful",
            data={
                "user": user_response.model_dump(),
                "tokens": token_data
            }
        )
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh-token", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_async_db)
):
    """Refresh access token using refresh token"""
    try:
        auth_service = AuthService(db)
        
        access_token, refresh_token = await auth_service.refresh_access_token(
            token_data.refresh_token
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout", response_model=ApiResponse)
async def logout_user(
    logout_data: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Logout user and revoke session(s)"""
    try:
        auth_service = AuthService(db)
        
        success = await auth_service.revoke_session(
            session_token=credentials.credentials,
            user_id=current_user.id,
            revoke_all=logout_data.logout_all_devices
        )
        
        message = "Logged out successfully"
        if logout_data.logout_all_devices:
            message = "Logged out from all devices successfully"
        
        return ApiResponse(
            success=success,
            message=message
        )
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


# User profile endpoints
@router.get("/me", response_model=UserApiResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get current user profile"""
    try:
        user_service = UserService(db)
        user = await user_service.get_user_by_id(current_user.id)
        
        user_response = UserProfile.model_validate(user)
        
        return UserApiResponse(
            success=True,
            message="User profile retrieved successfully",
            data=user_response
        )
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )


@router.put("/me", response_model=UserApiResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update current user profile"""
    try:
        user_service = UserService(db)
        
        updated_user = await user_service.update_user(current_user.id, user_data)
        user_response = UserResponse.model_validate(updated_user)
        
        return UserApiResponse(
            success=True,
            message="User profile updated successfully",
            data=user_response
        )
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )


@router.post("/change-password", response_model=ApiResponse)
async def change_user_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Change user password"""
    try:
        user_service = UserService(db)
        
        success = await user_service.change_password(current_user.id, password_data)
        
        return ApiResponse(
            success=success,
            message="Password changed successfully. Please log in again."
        )
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


# User preferences endpoints
@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get user preferences"""
    try:
        preferences_service = UserPreferencesService(db)
        
        preferences = await preferences_service.get_user_preferences(current_user.id)
        if not preferences:
            # Create default preferences if they don't exist
            preferences = await preferences_service.update_user_preferences(
                current_user.id, 
                UserPreferencesUpdate()
            )
        
        return UserPreferencesResponse.model_validate(preferences)
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user preferences"
        )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    preferences_data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Update user preferences"""
    try:
        preferences_service = UserPreferencesService(db)
        
        preferences = await preferences_service.update_user_preferences(
            current_user.id, 
            preferences_data
        )
        
        return UserPreferencesResponse.model_validate(preferences)
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user preferences"
        )


@router.post("/preferences/reset", response_model=UserPreferencesResponse)
async def reset_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Reset user preferences to defaults"""
    try:
        preferences_service = UserPreferencesService(db)
        
        preferences = await preferences_service.reset_user_preferences(current_user.id)
        
        return UserPreferencesResponse.model_validate(preferences)
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset user preferences"
        )


# Session management endpoints
@router.get("/sessions", response_model=List[UserSessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Get all active sessions for current user"""
    try:
        user_service = UserService(db)
        
        sessions = await user_service.get_user_sessions(current_user.id)
        
        return [UserSessionResponse.model_validate(session) for session in sessions]
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions"
        )


@router.delete("/sessions/{session_id}", response_model=ApiResponse)
async def revoke_user_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Revoke a specific user session"""
    try:
        auth_service = AuthService(db)
        
        # Find the session to get its token
        user_service = UserService(db)
        sessions = await user_service.get_user_sessions(current_user.id)
        
        target_session = next((s for s in sessions if s.id == session_id), None)
        if not target_session:
            raise ResourceNotFoundError("Session", str(session_id))
        
        success = await auth_service.revoke_session(
            session_token=target_session.session_token,
            user_id=current_user.id,
            revoke_all=False
        )
        
        return ApiResponse(
            success=success,
            message="Session revoked successfully"
        )
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )


# Account management endpoints
@router.post("/deactivate", response_model=ApiResponse)
async def deactivate_user_account(
    deactivation_data: dict,  # {password: str, reason?: str}
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Deactivate user account"""
    try:
        user_service = UserService(db)
        
        success = await user_service.deactivate_user(
            user_id=current_user.id,
            password=deactivation_data.get("password"),
            reason=deactivation_data.get("reason")
        )
        
        return ApiResponse(
            success=success,
            message="Account deactivated successfully"
        )
        
    except StudySprintException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate account"
        )


# Public endpoints (no authentication required)
@router.get("/check-email/{email}", response_model=dict)
async def check_email_availability(
    email: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Check if email is available for registration"""
    try:
        user_service = UserService(db)
        
        user = await user_service.get_user_by_email(email)
        available = user is None
        
        return {
            "available": available,
            "email": email
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check email availability"
        )


@router.get("/check-username/{username}", response_model=dict)
async def check_username_availability(
    username: str,
    db: AsyncSession = Depends(get_async_db)
):
    """Check if username is available for registration"""
    try:
        user_service = UserService(db)
        
        user = await user_service.get_user_by_username(username)
        available = user is None
        
        return {
            "available": available,
            "username": username
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check username availability"
        )


# Health check endpoint for the users module
@router.get("/health", response_model=dict)
async def users_health_check():
    """Health check for users module"""
    return {
        "module": "users",
        "status": "healthy",
        "version": "1.0.0"
    }
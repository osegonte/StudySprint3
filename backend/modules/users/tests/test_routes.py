# backend/modules/users/tests/test_routes.py
"""Tests for user API routes"""

import pytest
from fastapi.testclient import TestClient

from modules.users.schemas import UserCreate


class TestAuthRoutes:
    """Test authentication routes"""
    
    def test_register_user_success(self, client: TestClient):
        """Test successful user registration"""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "full_name": "New User",
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "user" in data["data"]
        assert "tokens" in data["data"]
        assert data["data"]["user"]["email"] == user_data["email"]
    
    def test_register_user_duplicate_email(self, client: TestClient, test_user):
        """Test registration with duplicate email"""
        user_data = {
            "email": test_user.email,
            "username": "differentuser",
            "password": "Password123!",
            "confirm_password": "Password123!"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_register_user_invalid_password(self, client: TestClient):
        """Test registration with invalid password"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",  # Too weak
            "confirm_password": "weak"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        assert response.status_code == 422
    
    def test_login_success(self, client: TestClient, test_user):
        """Test successful login"""
        login_data = {
            "email_or_username": test_user.email,
            "password": "TestPassword123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tokens" in data["data"]
        assert "user" in data["data"]
    
    def test_login_wrong_password(self, client: TestClient, test_user):
        """Test login with wrong password"""
        login_data = {
            "email_or_username": test_user.email,
            "password": "WrongPassword123!"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
    
    def test_logout_success(self, client: TestClient, auth_headers):
        """Test successful logout"""
        logout_data = {"logout_all_devices": False}
        
        response = client.post(
            "/api/v1/auth/logout", 
            json=logout_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestUserProfileRoutes:
    """Test user profile routes"""
    
    def test_get_current_user(self, client: TestClient, auth_headers, test_user):
        """Test getting current user profile"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == test_user.email
    
    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without authorization"""
        response = client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    def test_update_user_profile(self, client: TestClient, auth_headers):
        """Test updating user profile"""
        update_data = {
            "full_name": "Updated Name"
        }
        
        response = client.put(
            "/api/v1/auth/me",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["full_name"] == "Updated Name"
    
    def test_change_password_success(self, client: TestClient, auth_headers):
        """Test successful password change"""
        password_data = {
            "current_password": "TestPassword123!",
            "new_password": "NewPassword123!",
            "confirm_new_password": "NewPassword123!"
        }
        
        response = client.post(
            "/api/v1/auth/change-password",
            json=password_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestUserPreferencesRoutes:
    """Test user preferences routes"""
    
    def test_get_user_preferences(self, client: TestClient, auth_headers):
        """Test getting user preferences"""
        response = client.get("/api/v1/auth/preferences", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "theme" in data
        assert "language" in data
    
    def test_update_user_preferences(self, client: TestClient, auth_headers):
        """Test updating user preferences"""
        update_data = {
            "theme": "dark",
            "default_study_duration": 30
        }
        
        response = client.put(
            "/api/v1/auth/preferences",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"
        assert data["default_study_duration"] == 30


class TestPublicRoutes:
    """Test public routes"""
    
    def test_check_email_availability_available(self, client: TestClient):
        """Test checking available email"""
        response = client.get("/api/v1/auth/check-email/available@example.com")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
    
    def test_check_email_availability_taken(self, client: TestClient, test_user):
        """Test checking taken email"""
        response = client.get(f"/api/v1/auth/check-email/{test_user.email}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
    
    def test_check_username_availability_available(self, client: TestClient):
        """Test checking available username"""
        response = client.get("/api/v1/auth/check-username/available_username")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
    
    def test_check_username_availability_taken(self, client: TestClient, test_user):
        """Test checking taken username"""
        response = client.get(f"/api/v1/auth/check-username/{test_user.username}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False

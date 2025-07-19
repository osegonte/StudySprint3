# backend/common/errors.py
"""Custom exception handling for StudySprint 3.0"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class StudySprintException(Exception):
    """Base exception class for StudySprint application"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# Authentication Exceptions
class AuthenticationError(StudySprintException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_ERROR",
            details=details
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid login credentials"""
    
    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(
            message=message,
            details={"error_code": "INVALID_CREDENTIALS"}
        )


class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            message=message,
            details={"error_code": "TOKEN_EXPIRED"}
        )


class InvalidTokenError(AuthenticationError):
    """Invalid JWT token"""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(
            message=message,
            details={"error_code": "INVALID_TOKEN"}
        )


# Authorization Exceptions
class AuthorizationError(StudySprintException):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="AUTHORIZATION_ERROR",
            details=details
        )


class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permissions"""
    
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            details={"error_code": "INSUFFICIENT_PERMISSIONS"}
        )


# Validation Exceptions
class ValidationError(StudySprintException):
    """Input validation errors"""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        validation_details = details or {}
        if field:
            validation_details["field"] = field
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=validation_details
        )


class DuplicateResourceError(ValidationError):
    """Resource already exists"""
    
    def __init__(self, resource: str, field: str):
        super().__init__(
            message=f"{resource} with this {field} already exists",
            field=field,
            details={"error_code": "DUPLICATE_RESOURCE", "resource": resource}
        )


# Resource Exceptions
class ResourceNotFoundError(StudySprintException):
    """Resource not found"""
    
    def __init__(self, resource: str, identifier: str = None, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found"
        if identifier:
            message += f" with identifier: {identifier}"
        
        resource_details = details or {}
        resource_details.update({"resource": resource, "identifier": identifier})
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details=resource_details
        )


class ResourceConflictError(StudySprintException):
    """Resource conflict (e.g., trying to delete resource with dependencies)"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            details=details
        )


# File Operation Exceptions
class FileOperationError(StudySprintException):
    """File operation related errors"""
    
    def __init__(self, message: str, operation: str, details: Optional[Dict[str, Any]] = None):
        file_details = details or {}
        file_details["operation"] = operation
        
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="FILE_OPERATION_ERROR",
            details=file_details
        )


class FileNotFoundError(FileOperationError):
    """File not found"""
    
    def __init__(self, file_path: str):
        super().__init__(
            message=f"File not found: {file_path}",
            operation="read",
            details={"file_path": file_path}
        )


class FileUploadError(FileOperationError):
    """File upload failed"""
    
    def __init__(self, message: str = "File upload failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            operation="upload",
            details=details
        )


class FileSizeExceededError(FileUploadError):
    """File size exceeds limit"""
    
    def __init__(self, size: int, max_size: int):
        super().__init__(
            message=f"File size {size} bytes exceeds maximum allowed size of {max_size} bytes",
            details={
                "size": size,
                "max_size": max_size,
                "error_code": "FILE_SIZE_EXCEEDED"
            }
        )


class InvalidFileTypeError(FileUploadError):
    """Invalid file type"""
    
    def __init__(self, file_type: str, allowed_types: list):
        super().__init__(
            message=f"File type '{file_type}' not allowed. Allowed types: {', '.join(allowed_types)}",
            details={
                "file_type": file_type,
                "allowed_types": allowed_types,
                "error_code": "INVALID_FILE_TYPE"
            }
        )


# Database Exceptions
class DatabaseError(StudySprintException):
    """Database operation errors"""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details
        )


class DatabaseConnectionError(DatabaseError):
    """Database connection failed"""
    
    def __init__(self, message: str = "Failed to connect to database"):
        super().__init__(
            message=message,
            details={"error_code": "DATABASE_CONNECTION_ERROR"}
        )


# Business Logic Exceptions
class BusinessLogicError(StudySprintException):
    """Business logic validation errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details
        )


class SessionActiveError(BusinessLogicError):
    """Trying to start session when one is already active"""
    
    def __init__(self, session_id: str):
        super().__init__(
            message="Cannot start new session while another session is active",
            details={"active_session_id": session_id, "error_code": "SESSION_ACTIVE"}
        )


class SessionNotActiveError(BusinessLogicError):
    """Trying to perform operation on non-active session"""
    
    def __init__(self, session_id: str = None):
        message = "No active session found"
        details = {"error_code": "SESSION_NOT_ACTIVE"}
        if session_id:
            message = f"Session {session_id} is not active"
            details["session_id"] = session_id
        
        super().__init__(message=message, details=details)


# Rate Limiting Exceptions
class RateLimitError(StudySprintException):
    """Rate limit exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None):
        details = {"error_code": "RATE_LIMIT_EXCEEDED"}
        if retry_after:
            details["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_ERROR",
            details=details
        )


# Utility functions for error handling
def handle_database_error(error: Exception) -> StudySprintException:
    """Convert database errors to StudySprint exceptions"""
    error_str = str(error).lower()
    
    if "unique constraint" in error_str or "duplicate key" in error_str:
        return DuplicateResourceError("Resource", "field")
    elif "foreign key constraint" in error_str:
        return ResourceConflictError("Cannot perform operation due to existing dependencies")
    elif "connection" in error_str:
        return DatabaseConnectionError()
    else:
        return DatabaseError(f"Database operation failed: {str(error)}")


def handle_file_error(error: Exception, operation: str = "unknown") -> StudySprintException:
    """Convert file operation errors to StudySprint exceptions"""
    error_str = str(error).lower()
    
    if "no such file" in error_str or "file not found" in error_str:
        return FileNotFoundError("Unknown file")
    elif "permission denied" in error_str:
        return FileOperationError("Permission denied", operation)
    elif "disk space" in error_str or "no space left" in error_str:
        return FileOperationError("Insufficient disk space", operation)
    else:
        return FileOperationError(f"File operation failed: {str(error)}", operation)
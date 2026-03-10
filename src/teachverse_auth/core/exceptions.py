# teachverse_auth/core/exceptions.py
from fastapi import HTTPException, status
from typing import Optional

class AuthException(HTTPException):
    """Base authentication exception"""
    def __init__(
        self,
        status_code: int,
        detail: str = None,
        headers: Optional[dict] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)

class InvalidCredentialsError(AuthException):
    """Invalid username/password"""
    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )

class TokenExpiredError(AuthException):
    """Token has expired"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )

class InvalidTokenError(AuthException):
    """Token is invalid"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )

class PermissionDeniedError(AuthException):
    """User lacks required permission"""
    def __init__(self, permission: str = ""):
        detail = f"Permission denied: {permission}" if permission else "Permission denied"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )

class UserNotFoundError(AuthException):
    """User not found"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

class UserInactiveError(AuthException):
    """User account is inactive"""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

class DuplicateEntryError(AuthException):
    """Duplicate entry (email, phone, etc.)"""
    def __init__(self, field: str = ""):
        detail = f"{field} already exists" if field else "Entry already exists"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

class ServiceNotFoundError(AuthException):
    """Service not registered"""
    def __init__(self, service: str = ""):
        detail = f"Service '{service}' not found" if service else "Service not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )

class ResourceNotFoundError(AuthException):
    """Resource not found"""
    def __init__(self, resource: str = ""):
        detail = f"Resource '{resource}' not found" if resource else "Resource not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
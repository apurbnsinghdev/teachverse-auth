# teachverse_auth/core/__init__.py
from .config import settings
from .database import engine, get_db, init_db
from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_secure_key,
    generate_api_key,
    hash_api_key,
    verify_api_key
)
from .exceptions import (
    AuthException,
    InvalidCredentialsError,
    TokenExpiredError,
    InvalidTokenError,
    PermissionDeniedError,
    UserNotFoundError,
    UserInactiveError,
    DuplicateEntryError,
    ServiceNotFoundError,
    ResourceNotFoundError
)

__all__ = [
    "settings",
    "engine",
    "get_db",
    "init_db",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "create_refresh_token",
    "verify_token",
    "generate_secure_key",
    "generate_api_key",
    "hash_api_key",
    "verify_api_key",
    "AuthException",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "InvalidTokenError",
    "PermissionDeniedError",
    "UserNotFoundError",
    "UserInactiveError",
    "DuplicateEntryError",
    "ServiceNotFoundError",
    "ResourceNotFoundError",
]
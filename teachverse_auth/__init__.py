"""TEACHVERSE Auth - Production-ready authentication for FastAPI"""

__version__ = "0.1.0"
__author__ = "TEACHVERSE Team"

from .core.config import settings
from .core.database import engine, get_db
from .dependencies.auth import (
    get_current_user,
    get_optional_user,
    require_permission,
    require_resource_permission,
    require_role,
)

__all__ = [
    "settings",
    "engine",
    "get_db",
    "get_current_user",
    "get_optional_user",
    "require_permission",
    "require_resource_permission",
    "require_role",
]
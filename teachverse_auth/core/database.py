# teachverse_auth/core/database.py
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from .config import settings

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=30
)

def get_db() -> Generator[Session, None, None]:
    """Get database session"""
    with Session(engine) as session:
        yield session

def init_db() -> None:
    """Initialize database tables"""
    # Import all models to ensure they're registered with SQLModel
    from ..models import (
        User, UserRoleLink, UserPermissionLink,
        Organization, OrganizationSettings,
        Role, RolePermissionLink,
        Permission, ServiceRegistry, ResourceInstance
    )
    SQLModel.metadata.create_all(engine)

def drop_db() -> None:
    """Drop all tables (for testing)"""
    SQLModel.metadata.drop_all(engine)
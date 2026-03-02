# teachverse_auth/models/user.py
from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import enum

if TYPE_CHECKING:
    from .permission import Permission
    from .role import Role

class UserRole(str, enum.Enum):
    PLATFORM_ADMIN = "platform_admin"
    ORG_ADMIN = "org_admin"
    TEACHER = "teacher"
    STUDENT = "student"
    PARENT = "parent"
    SERVICE = "service"

class UserStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    phone: Optional[str] = Field(default=None, unique=True, index=True)
    full_name: str = Field(nullable=False)
    avatar_url: Optional[str] = Field(default=None)
    
    password_hash: str = Field(nullable=False)
    role: UserRole = Field(default=UserRole.STUDENT)
    status: UserStatus = Field(default=UserStatus.PENDING)
    
    organization_id: Optional[int] = Field(default=None, foreign_key="organizations.id")
    
    is_email_verified: bool = Field(default=False)
    is_phone_verified: bool = Field(default=False)
    last_login_at: Optional[datetime] = Field(default=None)
    last_login_ip: Optional[str] = Field(default=None)
    
    user_metadata: dict = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

class UserRoleLink(SQLModel, table=True):
    """Link between users and roles"""
    __tablename__ = "user_roles"
    
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    assigned_at: datetime = Field(default_factory=datetime.utcnow)

class UserPermissionLink(SQLModel, table=True):
    """Direct permissions assigned to users"""
    __tablename__ = "user_permissions"
    
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)
    granted_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(default=None)
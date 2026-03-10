# teachverse_auth/models/role.py
from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user import User
    from .permission import Permission

class Role(SQLModel, table=True):
    __tablename__ = "roles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, nullable=False)
    description: Optional[str] = Field(default=None)
    level: int = Field(default=0)
    
    organization_id: Optional[int] = Field(default=None, foreign_key="organizations.id")
    
    is_system: bool = Field(default=False)
    is_default: bool = Field(default=False)
    
    role_metadata: dict = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class RolePermissionLink(SQLModel, table=True):
    """Link between roles and permissions"""
    __tablename__ = "role_permissions"
    
    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
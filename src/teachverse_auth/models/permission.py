# teachverse_auth/models/permission.py
from sqlmodel import SQLModel, Field, Column, JSON, Relationship
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .user import User
    from .role import Role

class Permission(SQLModel, table=True):
    __tablename__ = "permissions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    service: str = Field(index=True, nullable=False)
    resource_type: str = Field(index=True, nullable=False)
    resource_id: str = Field(default="*", index=True)
    action: str = Field(index=True, nullable=False)
    
    name: str = Field(unique=True, index=True)
    description: Optional[str] = Field(default=None)
    
    is_system: bool = Field(default=False)
    has_wildcard: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def __init__(self, **data):
        if all(k in data for k in ['service', 'resource_type', 'action']):
            resource_part = data.get('resource_id', '*')
            data['name'] = f"{data['service']}:{data['resource_type']}:{resource_part}:{data['action']}"
            data['has_wildcard'] = '*' in str(resource_part)
        super().__init__(**data)

class ServiceRegistry(SQLModel, table=True):
    __tablename__ = "service_registry"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    service_name: str = Field(unique=True, index=True)
    display_name: str
    description: Optional[str] = None
    base_url: Optional[str] = None
    
    resource_types: List[str] = Field(sa_column=Column(JSON), default=[])
    available_actions: List[str] = Field(sa_column=Column(JSON), default=[])
    
    registry_metadata: dict = Field(default={}, sa_column=Column(JSON))
    is_active: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ResourceInstance(SQLModel, table=True):
    __tablename__ = "resource_instances"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    service: str = Field(index=True)
    resource_type: str = Field(index=True)
    resource_id: str = Field(index=True)
    display_name: str
    
    owner_id: Optional[int] = Field(default=None, index=True)
    owner_type: Optional[str] = Field(default=None)
    
    parent_id: Optional[int] = Field(default=None, foreign_key="resource_instances.id")
    
    instance_metadata: dict = Field(default={}, sa_column=Column(JSON))
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
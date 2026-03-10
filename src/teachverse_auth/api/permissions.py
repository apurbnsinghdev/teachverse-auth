from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional
from sqlmodel import Session, select

from ..models.permission import Permission, ServiceRegistry, ResourceInstance
from ..services.permission_service import PermissionService
from ..dependencies.auth import PermissionChecker, get_current_user, TokenData
from ..core.database import get_db
from pydantic import BaseModel
from datetime import datetime

router = APIRouter(prefix="/api/v1/permissions", tags=["permissions"])

class PermissionCreate(BaseModel):
    service: str
    resource_type: str
    resource_id: str = "*"
    action: str
    description: Optional[str] = None

class PermissionResponse(BaseModel):
    id: int
    name: str
    service: str
    resource_type: str
    resource_id: str
    action: str
    description: Optional[str]
    is_system: bool
    created_at: datetime

# This file defines API endpoints for managing permissions and services, as well as checking permissions for users. It uses the PermissionService for the underlying logic and interacts with the database to store and retrieve permissions and service registry information.
@router.post("/", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    current_user: TokenData = Depends(PermissionChecker("auth", "permission", "create")),
    db: Session = Depends(get_db)
):
    """
    Create a hierarchical permission like AWS IAM.
    """
    # Validate service exists
    service = db.exec(
        select(ServiceRegistry).where(ServiceRegistry.service_name == permission_data.service)
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=400,
            detail=f"Service '{permission_data.service}' not registered"
        )
    
    # Validate resource type
    if permission_data.resource_type not in service.resource_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid resource type. Valid: {service.resource_types}"
        )
    
    # Validate action
    if permission_data.action != "*" and permission_data.action not in service.available_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Valid: {service.available_actions}"
        )
    
    # Check if permission already exists
    existing = db.exec(
        select(Permission).where(
            Permission.service == permission_data.service,
            Permission.resource_type == permission_data.resource_type,
            Permission.resource_id == permission_data.resource_id,
            Permission.action == permission_data.action
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Permission already exists"
        )
    
    # Create permission
    permission = Permission(
        service=permission_data.service,
        resource_type=permission_data.resource_type,
        resource_id=permission_data.resource_id,
        action=permission_data.action,
        description=permission_data.description
    )
    
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
    return permission

@router.get("/check")
async def check_user_permission(
    service: str,
    resource_type: str,
    resource_id: str,
    action: str,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if current user has a specific permission"""
    has_perm = await PermissionService.check_permission(
        db=db,
        user_id=int(current_user.sub),
        service=service,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action
    )
    
    return {"has_permission": has_perm}

@router.get("/my")
async def get_my_permissions(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all permissions for current user"""
    permissions = await PermissionService.get_user_permissions(
        db=db,
        user_id=int(current_user.sub)
    )
    
    return {"permissions": list(permissions)}

@router.get("/services", response_model=List[ServiceRegistry])
async def list_services(
    current_user: TokenData = PermissionChecker("auth", "service", "list"), 
    db: Session = Depends(get_db)
):
    """List all registered services"""
    services = db.exec(select(ServiceRegistry)).all()
    return services
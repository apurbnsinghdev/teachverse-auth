from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional
from sqlmodel import Session, select

from ..models.permission import Permission, ServiceRegistry, ResourceInstance
from ..services.permission_service import PermissionService
from ..dependencies.auth import require_permission, get_current_user, TokenData
from ..core.database import get_db

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

@router.post("", response_model=PermissionResponse)
async def create_permission(
    permission_data: PermissionCreate,
    current_user = Depends(require_permission("auth", "permission", "create")),
    db: Session = Depends(get_db)
):
    """
    Create a hierarchical permission like AWS IAM.
    
    Examples:
        - Read any course: 
          {"service": "course", "resource_type": "course", "resource_id": "*", "action": "read"}
        - Update specific course:
          {"service": "course", "resource_type": "course", "resource_id": "123", "action": "update"}
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

@router.post("/services/register")
async def register_service(
    service_name: str = Body(...),
    display_name: str = Body(...),
    resource_types: List[str] = Body(...),
    actions: List[str] = Body(...),
    base_url: Optional[str] = Body(None),
    current_user = Depends(require_permission("auth", "service", "register")),
    db: Session = Depends(get_db)
):
    """Register a new service (called by microservices)"""
    registry = await PermissionService.register_service(
        db=db,
        service_name=service_name,
        display_name=display_name,
        resource_types=resource_types,
        actions=actions,
        base_url=base_url
    )
    
    return registry

@router.get("/services", response_model=List[ServiceRegistry])
async def list_services(
    current_user = Depends(require_permission("auth", "service", "list")),
    db: Session = Depends(get_db)
):
    """List all registered services"""
    services = db.exec(select(ServiceRegistry)).all()
    return services
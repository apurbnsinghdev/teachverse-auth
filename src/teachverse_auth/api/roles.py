# teachverse_auth/api/roles.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime

from ..core.database import get_db
from ..core.security import TokenData
from ..dependencies.auth import get_current_user, PermissionChecker
from ..models.role import Role, RolePermissionLink
from ..models.permission import Permission
from ..models.user import UserRoleLink
from ..services.permission_service import PermissionService

router = APIRouter(prefix="/api/v1/roles", tags=["roles"])

# ========== Pydantic Models ==========

from pydantic import BaseModel

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    level: int = 0
    permission_ids: List[int] = []
    is_default: bool = False

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    level: Optional[int] = None
    is_default: Optional[bool] = None

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    level: int
    is_system: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

class RoleDetailResponse(RoleResponse):
    permissions: List[dict] = []

# ========== Role Endpoints ==========

@router.get("/", response_model=List[RoleResponse])
async def list_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: TokenData = Depends(PermissionChecker("auth", "role", "list")),
    db: Session = Depends(get_db)
):
    """List all roles (requires auth:role:list permission)"""
    roles = db.exec(select(Role).offset(skip).limit(limit)).all()
    return roles

@router.get("/{role_id}", response_model=RoleDetailResponse)
async def get_role(
    role_id: int,
    current_user: TokenData = Depends(PermissionChecker("auth", "role", "read")),
    db: Session = Depends(get_db)
):
    """Get role by ID with its permissions"""
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Get permissions for this role
    permissions = db.exec(
        select(Permission)
        .join(RolePermissionLink)
        .where(RolePermissionLink.role_id == role_id)
    ).all()
    
    return {
        **role.dict(),
        "permissions": [{"id": p.id, "name": p.name} for p in permissions]
    }

@router.post("/", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    current_user: TokenData = Depends(PermissionChecker("auth", "role", "create")),
    db: Session = Depends(get_db)
):
    """Create a new role (requires auth:role:create permission)"""
    # Check if role with same name exists
    existing = db.exec(
        select(Role).where(Role.name == role_data.name)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with name '{role_data.name}' already exists"
        )
    
    # Create role
    role = Role(
        name=role_data.name,
        description=role_data.description,
        level=role_data.level,
        is_default=role_data.is_default,
        is_system=False
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    
    # Assign permissions
    for perm_id in role_data.permission_ids:
        perm = db.get(Permission, perm_id)
        if perm:
            role_perm = RolePermissionLink(role_id=role.id, permission_id=perm_id)
            db.add(role_perm)
    
    db.commit()
    db.refresh(role)
    
    return role

@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: TokenData = Depends(PermissionChecker("auth", "role", "update")),
    db: Session = Depends(get_db)
):
    """Update an existing role (requires auth:role:update permission)"""
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Don't allow updating system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system roles"
        )
    
    # Update fields
    if role_data.name is not None:
        # Check if new name conflicts
        existing = db.exec(
            select(Role).where(Role.name == role_data.name, Role.id != role_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role with name '{role_data.name}' already exists"
            )
        role.name = role_data.name
    
    if role_data.description is not None:
        role.description = role_data.description
    
    if role_data.level is not None:
        role.level = role_data.level
    
    if role_data.is_default is not None:
        role.is_default = role_data.is_default
    
    role.updated_at = datetime.utcnow()
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return role

@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    current_user: TokenData = Depends(PermissionChecker("auth", "role", "delete")),
    db: Session = Depends(get_db)
):
    """Delete a role (requires auth:role:delete permission)"""
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Don't allow deleting system roles
    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system roles"
        )
    
    # Check if role is assigned to any users
    user_count = db.exec(
        select(UserRoleLink).where(UserRoleLink.role_id == role_id)
    ).count()
    
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role assigned to {user_count} users"
        )
    
    # Delete role permissions links
    db.exec(
        select(RolePermissionLink).where(RolePermissionLink.role_id == role_id)
    ).delete()
    
    # Delete role
    db.delete(role)
    db.commit()
    
    return {"message": "Role deleted successfully"}

@router.post("/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: int,
    permission_ids: List[int],
    current_user: TokenData = Depends(PermissionChecker("auth", "role", "update")),
    db: Session = Depends(get_db)
):
    """Assign permissions to a role"""
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Remove existing permissions
    db.exec(
        select(RolePermissionLink).where(RolePermissionLink.role_id == role_id)
    ).delete()
    
    # Add new permissions
    for perm_id in permission_ids:
        perm = db.get(Permission, perm_id)
        if perm:
            role_perm = RolePermissionLink(role_id=role_id, permission_id=perm_id)
            db.add(role_perm)
    
    db.commit()
    
    return {"message": f"Assigned {len(permission_ids)} permissions to role"}

@router.get("/{role_id}/permissions")
async def get_role_permissions(
    role_id: int,
    current_user: TokenData = Depends(PermissionChecker("auth", "role", "read")),
    db: Session = Depends(get_db)
):
    """Get all permissions for a role"""
    role = db.get(Role, role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    permissions = db.exec(
        select(Permission)
        .join(RolePermissionLink)
        .where(RolePermissionLink.role_id == role_id)
    ).all()
    
    return permissions
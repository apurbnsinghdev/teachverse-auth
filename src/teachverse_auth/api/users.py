# teachverse_auth/api/users.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

from ..core.database import get_db
from ..core.security import (
    get_password_hash,
    verify_password,
)
from ..dependencies.auth import (
    get_current_user,
    PermissionChecker,
    TokenData
)
from ..models.user import User, UserRole, UserStatus, UserRoleLink, UserPermissionLink
from ..models.role import Role
from ..models.permission import Permission
from ..services.permission_service import PermissionService

router = APIRouter(prefix="/api/v1/users", tags=["users"])

# ========== Pydantic Models ==========
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None
    role: Optional[UserRole] = UserRole.STUDENT
    organization_id: Optional[int] = None

    model_config = ConfigDict(use_enum_values=True)

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    organization_id: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    status: UserStatus
    organization_id: Optional[int] = None
    is_email_verified: bool
    is_phone_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True
    )

class UserDetailResponse(UserResponse):
    roles: List[dict] = []
    permissions: List[str] = []

    model_config = ConfigDict(from_attributes=True)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class AssignRoleRequest(BaseModel):
    role_id: int

class AssignPermissionRequest(BaseModel):
    permission_id: int

# ========== Helper to get user roles ==========
async def _get_user_roles(db: Session, user_id: int) -> List[dict]:
    """Helper to get user roles"""
    role_links = db.exec(
        select(UserRoleLink).where(UserRoleLink.user_id == user_id)
    ).all()
    roles = []
    for link in role_links:
        role = db.get(Role, link.role_id)
        if role:
            roles.append({"id": role.id, "name": role.name})
    return roles

# ========== User Endpoints ==========
@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    organization_id: Optional[int] = None,
    current_user: TokenData = Depends(PermissionChecker("auth", "user", "list")), 
    db: Session = Depends(get_db)
):
    """List all users with optional filters (requires auth:user:list permission)"""
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    if status:
        query = query.where(User.status == status)
    if organization_id:
        query = query.where(User.organization_id == organization_id)
    
    users = db.exec(query.offset(skip).limit(limit)).all()
    return users

@router.get("/me", response_model=UserDetailResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information"""
    user = db.get(User, int(current_user.sub))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user roles
    roles = await _get_user_roles(db, user.id)
    
    # Get user permissions
    permissions = await PermissionService.get_user_permissions(db, user.id)
    
    return {
        **user.model_dump(),
        "roles": roles,
        "permissions": list(permissions)
    }

@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user(
    user_id: int,
    current_user: TokenData = Depends(PermissionChecker("auth", "user", "read")),
    db: Session = Depends(get_db)
):
    """Get user by ID (requires auth:user:read permission)"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user roles
    roles = await _get_user_roles(db, user_id)
    
    # Get user permissions
    permissions = await PermissionService.get_user_permissions(db, user_id)
    
    return {
        **user.model_dump(),
        "roles": roles,
        "permissions": list(permissions)
    }

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    create_user: TokenData = Depends(PermissionChecker("auth", "user", "create")),
    db: Session = Depends(get_db)
):
    """Create a new user (requires auth:user:create permission)"""
    # Check if user exists
    existing = db.exec(
        select(User).where(User.email == user_data.email)
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    if user_data.phone:
        existing_phone = db.exec(
            select(User).where(User.phone == user_data.phone)
        ).first()
        if existing_phone:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone already registered"
            )
    
    # Create user
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        password_hash=get_password_hash(user_data.password),
        role=user_data.role,
        organization_id=user_data.organization_id,
        status=UserStatus.ACTIVE  # Admin-created users are active by default
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Assign default role (student)
    default_role = db.exec(
        select(Role).where(Role.is_default == True)
    ).first()
    if default_role:
        user_role = UserRoleLink(user_id=user.id, role_id=default_role.id)
        db.add(user_role)
        db.commit()
    
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    create_user: TokenData = Depends(PermissionChecker("auth", "user", "update")),
    db: Session = Depends(get_db)
):
    """Update user information (requires auth:user:update permission)"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    if user_data.phone is not None:
        # Check if phone is taken
        if user_data.phone != user.phone:
            existing = db.exec(
                select(User).where(User.phone == user_data.phone, User.id != user_id)
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Phone already registered"
                )
        user.phone = user_data.phone
    if user_data.avatar_url is not None:
        user.avatar_url = user_data.avatar_url
    if user_data.organization_id is not None:
        user.organization_id = user_data.organization_id
    
    user.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    create_user: TokenData = Depends(PermissionChecker("auth", "user", "delete")),
    db: Session = Depends(get_db)
):
    """Delete a user (requires auth:user:delete permission)"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Soft delete
    user.status = UserStatus.DELETED
    user.deleted_at = datetime.utcnow()
    db.add(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@router.post("/{user_id}/change-password")
async def change_password(
    user_id: int,
    password_data: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password (users can only change their own password)"""
    # Only allow users to change their own password unless admin
    if int(current_user.sub) != user_id and "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot change another user's password"
        )
    
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    user.password_hash = get_password_hash(password_data.new_password)
    user.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/{user_id}/roles")
async def assign_role_to_user(
    user_id: int,
    role_data: AssignRoleRequest,
    current_user: TokenData = Depends(PermissionChecker("auth", "user", "update")),
    db: Session = Depends(get_db)
):
    """Assign a role to a user"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role = db.get(Role, role_data.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    # Check if already assigned
    existing = db.exec(
        select(UserRoleLink).where(
            UserRoleLink.user_id == user_id,
            UserRoleLink.role_id == role_data.role_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role already assigned to user"
        )
    
    # Assign role
    user_role = UserRoleLink(user_id=user_id, role_id=role_data.role_id)
    db.add(user_role)
    db.commit()
    
    return {"message": f"Role '{role.name}' assigned to user"}

@router.delete("/{user_id}/roles/{role_id}")
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    current_user: TokenData = Depends(PermissionChecker("auth", "user", "update")),
    db: Session = Depends(get_db)
):
    """Remove a role from a user"""
    user_role = db.exec(
        select(UserRoleLink).where(
            UserRoleLink.user_id == user_id,
            UserRoleLink.role_id == role_id
        )
    ).first()
    
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not assigned to user"
        )
    
    db.delete(user_role)
    db.commit()
    
    return {"message": "Role removed from user"}

@router.get("/{user_id}/permissions")
async def get_user_permissions(
    user_id: int,
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all permissions for a user"""
    # Users can view their own permissions, admins can view any
    if int(current_user.sub) != user_id and "admin" not in current_user.scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view another user's permissions"
        )
    
    permissions = await PermissionService.get_user_permissions(db, user_id)
    return {"permissions": list(permissions)}

@router.post("/{user_id}/permissions")
async def assign_permission_to_user(
    user_id: int,
    permission_data: AssignPermissionRequest,
    current_user: TokenData = Depends(PermissionChecker("auth", "permission", "assign")),
    db: Session = Depends(get_db)
):
    """Assign a direct permission to a user (bypasses roles)"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    permission = db.get(Permission, permission_data.permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found"
        )
    
    # Check if already assigned
    existing = db.exec(
        select(UserPermissionLink).where(
            UserPermissionLink.user_id == user_id,
            UserPermissionLink.permission_id == permission_data.permission_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission already assigned to user"
        )
    
    # Assign permission
    user_perm = UserPermissionLink(
        user_id=user_id,
        permission_id=permission_data.permission_id
    )
    db.add(user_perm)
    db.commit()
    
    return {"message": f"Permission '{permission.name}' assigned to user"}

@router.delete("/{user_id}/permissions/{permission_id}")
async def revoke_permission_from_user(
    user_id: int,
    permission_id: int,
    current_user: TokenData = Depends(PermissionChecker("auth", "permission", "assign")),
    db: Session = Depends(get_db)
):
    """Revoke a direct permission from a user"""
    user_perm = db.exec(
        select(UserPermissionLink).where(
            UserPermissionLink.user_id == user_id,
            UserPermissionLink.permission_id == permission_id
        )
    ).first()
    
    if not user_perm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not assigned to user"
        )
    
    db.delete(user_perm)
    db.commit()
    
    return {"message": "Permission revoked from user"}
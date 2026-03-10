from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.security import generate_secure_key, get_password_hash
from ..dependencies.auth import PermissionChecker, get_current_user, TokenData
from ..models.user import User, UserRole
from ..models.permission import Permission, ServiceRegistry
from ..models.role import Role
from ..services.permission_service import PermissionService
from ..core.exceptions import UserNotFoundError

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

@router.get("/stats")
async def get_admin_stats(
    _: TokenData = Depends(PermissionChecker("system", "stats", "read")),
    db: Session = Depends(get_db)
):
    """Get platform statistics"""
    total_users = db.exec(select(User)).count()
    total_roles = db.exec(select(Role)).count()
    total_permissions = db.exec(select(Permission)).count()
    total_services = db.exec(select(ServiceRegistry)).count()
    
    # Recent users (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_users = db.exec(
        select(User).where(User.created_at >= week_ago)
    ).count()
    
    return {
        "total_users": total_users,
        "total_roles": total_roles,
        "total_permissions": total_permissions,
        "total_services": total_services,
        "recent_users": recent_users,
        "active_sessions": 0,  # Would need Redis for this
    }

@router.get("/users")
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[str] = None,
    current_user: TokenData = Depends(PermissionChecker("user", "user", "list")),
    db: Session = Depends(get_db)
):
    """List all users with optional filters"""
    query = select(User)
    if role:
        query = query.where(User.role == role)
    
    users = db.exec(query.offset(skip).limit(limit)).all()
    return users

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    current_user: TokenData = Depends(PermissionChecker("user", "user", "update")),
    db: Session = Depends(get_db)
):
    """Reset user password (admin only)"""
    user = db.get(User, user_id)
    if not user:
        raise UserNotFoundError()
    
    # Generate temporary password
    temp_password = generate_secure_key(12)
    user.password_hash = get_password_hash(temp_password)
    db.add(user)
    db.commit()
    
    return {"message": "Password reset", "temporary_password": temp_password}

@router.post("/users/{user_id}/suspend")
async def suspend_user(
    user_id: int,
    reason: str = None,
    current_user: TokenData = Depends(PermissionChecker("user", "user", "suspend")),
    db: Session = Depends(get_db)
):
    """Suspend a user account"""
    user = db.get(User, user_id)
    if not user:
        raise UserNotFoundError()
    
    user.status = "suspended"
    user.metadata["suspension_reason"] = reason
    user.metadata["suspended_by"] = int(current_user.sub)
    user.metadata["suspended_at"] = datetime.utcnow().isoformat()
    
    db.add(user)
    db.commit()
    
    return {"message": "User suspended"}

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: TokenData = Depends(PermissionChecker("user", "user", "activate")),
    db: Session = Depends(get_db)
):
    """Activate a suspended user"""
    user = db.get(User, user_id)
    if not user:
        raise UserNotFoundError()
    
    user.status = "active"
    user.metadata["activated_by"] = int(current_user.sub)
    user.metadata["activated_at"] = datetime.utcnow().isoformat()
    
    db.add(user)
    db.commit()
    
    return {"message": "User activated"}

@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    current_user: TokenData = Depends(PermissionChecker("system", "audit", "read")),
    db: Session = Depends(get_db)
):
    """Get audit logs (requires audit permission)"""
    # This would need an AuditLog model
    return {"logs": [], "message": "Audit logging coming soon"}

@router.get("/health/services")
async def check_services_health(
    current_user: TokenData = Depends(PermissionChecker("system", "health", "read")),
    db: Session = Depends(get_db)
):
    """Check health of all registered services"""
    services = db.exec(select(ServiceRegistry)).all()
    health_status = {}
    
    for service in services:
        # In production, you'd actually ping each service
        health_status[service.service_name] = {
            "status": "unknown",
            "last_check": datetime.utcnow().isoformat(),
            "url": service.base_url
        }
    
    return health_status
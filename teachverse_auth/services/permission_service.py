# teachverse_auth/services/permission_service.py
from typing import List, Set, Optional
from sqlmodel import Session, select
import fnmatch
from datetime import datetime

from ..models.user import User, UserRoleLink, UserPermissionLink
from ..models.role import Role, RolePermissionLink
from ..models.permission import Permission, ServiceRegistry

class PermissionService:
    """Service for hierarchical permission checking like AWS IAM"""
    
    MANAGE_ACTIONS = ["create", "read", "update", "delete", "list", "publish", "archive", "restore"]
    
    @classmethod
    async def check_permission(
        cls,
        db: Session,
        user_id: int,
        service: str,
        resource_type: str,
        resource_id: str,
        action: str
    ) -> bool:
        """Check if user has permission on a specific resource"""
        user_perms = await cls.get_user_permissions(db, user_id)
        
        check_patterns = [
            f"{service}:{resource_type}:{resource_id}:{action}",
            f"{service}:{resource_type}:*:{action}",
            f"{service}:{resource_type}:{resource_id}:*",
            f"{service}:{resource_type}:*:*",
            f"{service}:*:*:*",
        ]
        
        if action in cls.MANAGE_ACTIONS:
            manage_patterns = [
                f"{service}:{resource_type}:{resource_id}:manage",
                f"{service}:{resource_type}:*:manage",
            ]
            for pattern in manage_patterns:
                if pattern in user_perms:
                    return True
        
        for pattern in check_patterns:
            if pattern in user_perms:
                return True
        
        for perm in user_perms:
            if fnmatch.fnmatch(f"{service}:{resource_type}:{resource_id}:{action}", perm):
                return True
        
        return False
    
    @classmethod
    async def get_user_permissions(cls, db: Session, user_id: int) -> Set[str]:
        """Get all permission names for a user"""
        # Role-based permissions
        role_perms = db.exec(
            select(Permission.name)
            .join(RolePermissionLink)
            .join(Role)
            .join(UserRoleLink)
            .where(UserRoleLink.user_id == user_id)
        ).all()
        
        # Direct permissions
        direct_perms = db.exec(
            select(Permission.name)
            .join(UserPermissionLink)
            .where(UserPermissionLink.user_id == user_id)
        ).all()
        
        return set(list(role_perms) + list(direct_perms))
    
    @classmethod
    async def register_service(
        cls,
        db: Session,
        service_name: str,
        display_name: str,
        resource_types: List[str],
        actions: List[str],
        base_url: Optional[str] = None
    ) -> ServiceRegistry:
        """Register a new service and create its default permissions"""
        registry = db.exec(
            select(ServiceRegistry).where(ServiceRegistry.service_name == service_name)
        ).first()
        
        if registry:
            registry.resource_types = resource_types
            registry.available_actions = actions
            registry.display_name = display_name
            registry.base_url = base_url
            registry.updated_at = datetime.utcnow()
        else:
            registry = ServiceRegistry(
                service_name=service_name,
                display_name=display_name,
                resource_types=resource_types,
                available_actions=actions,
                base_url=base_url
            )
            db.add(registry)
        
        db.commit()
        db.refresh(registry)
        
        await cls._create_service_permissions(db, service_name, resource_types, actions)
        
        return registry
    
    @classmethod
    async def _create_service_permissions(
        cls,
        db: Session,
        service: str,
        resource_types: List[str],
        actions: List[str]
    ) -> List[Permission]:
        """Create all standard permissions for a service"""
        permissions = []
        
        for resource_type in resource_types:
            for action in actions:
                existing = db.exec(
                    select(Permission).where(
                        Permission.service == service,
                        Permission.resource_type == resource_type,
                        Permission.resource_id == "*",
                        Permission.action == action
                    )
                ).first()
                
                if not existing:
                    perm = Permission(
                        service=service,
                        resource_type=resource_type,
                        resource_id="*",
                        action=action,
                        description=f"{action} any {resource_type} in {service} service",
                        is_system=True
                    )
                    db.add(perm)
                    permissions.append(perm)
        
        db.commit()
        return permissions
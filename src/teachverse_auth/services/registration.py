# teachverse_auth/services/registration.py
from typing import List, Optional
from sqlmodel import Session, select
from datetime import datetime

from ..models.permission import ServiceRegistry, Permission
from ..services.permission_service import PermissionService

class RegistrationService:
    """Service for handling service registration and permission creation"""
    
    @classmethod
    async def register_service(
        cls,
        db: Session,
        service_name: str,
        display_name: str,
        resource_types: List[str],
        actions: List[str],
        base_url: Optional[str] = None,
        description: Optional[str] = None
    ) -> ServiceRegistry:
        """
        Register a new service and create its default permissions
        """
        # Validate inputs
        if not service_name or not service_name.strip():
            raise ValueError("Service name cannot be empty")
        if not display_name:
            raise ValueError("Display name cannot be empty")
        if not resource_types:
            raise ValueError("At least one resource type is required")
        if not actions:
            raise ValueError("At least one action is required")
        
        # Check if service already exists
        existing = db.exec(
            select(ServiceRegistry).where(ServiceRegistry.service_name == service_name)
        ).first()
        
        if existing:
            raise ValueError(f"Service '{service_name}' already exists")
        
        # Create service registry entry
        registry = ServiceRegistry(
            service_name=service_name,
            display_name=display_name,
            description=description,
            resource_types=resource_types,
            available_actions=actions,
            base_url=base_url,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(registry)
        db.commit()
        db.refresh(registry)
        
        # Create default permissions for this service
        await cls._create_service_permissions(db, registry)
        
        return registry
    
    @classmethod
    async def _create_service_permissions(
        cls,
        db: Session,
        registry: ServiceRegistry
    ) -> List[Permission]:
        """Create all standard permissions for a service"""
        permissions = []
        
        for resource_type in registry.resource_types:
            for action in registry.available_actions:
                # Check if permission already exists
                existing = db.exec(
                    select(Permission).where(
                        Permission.service == registry.service_name,
                        Permission.resource_type == resource_type,
                        Permission.resource_id == "*",
                        Permission.action == action
                    )
                ).first()
                
                if not existing:
                    perm = Permission(
                        service=registry.service_name,
                        resource_type=resource_type,
                        resource_id="*",
                        action=action,
                        description=f"{action} any {resource_type} in {registry.service_name} service",
                        is_system=True,
                        created_at=datetime.utcnow()
                    )
                    db.add(perm)
                    permissions.append(perm)
        
        db.commit()
        
        # Refresh permissions to get IDs
        for perm in permissions:
            db.refresh(perm)
        
        return permissions
    
    @classmethod
    async def get_service_permissions(
        cls,
        db: Session,
        service_name: str
    ) -> List[Permission]:
        """Get all permissions for a specific service"""
        permissions = db.exec(
            select(Permission).where(Permission.service == service_name)
        ).all()
        return permissions
    
    @classmethod
    async def get_all_services(
        cls,
        db: Session,
        include_inactive: bool = False
    ) -> List[ServiceRegistry]:
        """Get all registered services"""
        query = select(ServiceRegistry)
        if not include_inactive:
            query = query.where(ServiceRegistry.is_active == True)
        
        services = db.exec(query).all()
        return services
    
    @classmethod
    async def update_service(
        cls,
        db: Session,
        service_name: str,
        **kwargs
    ) -> Optional[ServiceRegistry]:
        """Update service configuration"""
        service = db.exec(
            select(ServiceRegistry).where(ServiceRegistry.service_name == service_name)
        ).first()
        
        if not service:
            return None
        
        # Update allowed fields
        allowed_fields = ['display_name', 'description', 'resource_types', 
                         'available_actions', 'base_url', 'is_active']
        
        for field in allowed_fields:
            if field in kwargs:
                setattr(service, field, kwargs[field])
        
        service.updated_at = datetime.utcnow()
        db.add(service)
        db.commit()
        db.refresh(service)
        
        # If resource_types or actions changed, update permissions
        if 'resource_types' in kwargs or 'available_actions' in kwargs:
            await cls._sync_service_permissions(db, service)
        
        return service
    
    @classmethod
    async def _sync_service_permissions(
        cls,
        db: Session,
        registry: ServiceRegistry
    ):
        """Sync permissions when service configuration changes"""
        # Get existing permissions
        existing_perms = db.exec(
            select(Permission).where(Permission.service == registry.service_name)
        ).all()
        
        existing_keys = {
            (p.resource_type, p.action) for p in existing_perms
            if p.resource_id == "*"  # Only manage wildcard permissions
        }
        
        # Create new permissions
        new_keys = set()
        for resource_type in registry.resource_types:
            for action in registry.available_actions:
                new_keys.add((resource_type, action))
        
        # Add missing permissions
        for resource_type, action in new_keys - existing_keys:
            perm = Permission(
                service=registry.service_name,
                resource_type=resource_type,
                resource_id="*",
                action=action,
                description=f"{action} any {resource_type} in {registry.service_name} service",
                is_system=True,
                created_at=datetime.utcnow()
            )
            db.add(perm)
        
        # Note: We don't delete permissions automatically to avoid breaking existing assignments
        db.commit()
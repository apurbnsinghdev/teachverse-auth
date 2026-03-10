# teachverse_auth/api/services.py
# This file can be used for any additional service-related API endpoints that don't fit into auth or permissions.
from fastapi import APIRouter, Depends, HTTPException, status, Body
from typing import List, Optional
from sqlmodel import Session, select
from pydantic import BaseModel
from ..models.permission import Permission, ServiceRegistry
from ..services.permission_service import PermissionService
from ..dependencies.auth import PermissionChecker, get_current_user, TokenData
from ..models.permission import ServiceRegistry
from ..services.registration import RegistrationService
from ..core.database import get_db
from datetime import datetime

router = APIRouter(prefix="/api/v1/services", tags=["services"])

class ServiceRegisterRequest(BaseModel):
    service_name: str
    display_name: str
    resource_types: List[str]
    actions: List[str]
    base_url: Optional[str] = None
    description: Optional[str] = None

class ServiceResponse(BaseModel):
    id: int
    service_name: str
    display_name: str
    description: Optional[str]
    resource_types: List[str]
    available_actions: List[str]
    base_url: Optional[str]
    is_active: bool
    created_at: datetime

@router.post("/register", response_model=ServiceResponse)
async def register_service(
    request: ServiceRegisterRequest,
    current_user : TokenData = Depends(PermissionChecker("auth", "service", "register")),
    db: Session = Depends(get_db)
):
    """
    Register a new service with the auth system.
    This creates the service registry entry and generates default permissions.
    """
    try:
        registry = await RegistrationService.register_service(
            db=db,
            service_name=request.service_name,
            display_name=request.display_name,
            resource_types=request.resource_types,
            actions=request.actions,
            base_url=request.base_url,
            description=request.description
        )
        return registry
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ServiceResponse])
async def list_services(
    skip: int = 0,
    limit: int = 100,
    include_inactive: bool = False,
    current_user: TokenData = Depends(PermissionChecker("auth", "service", "list")),
    db: Session = Depends(get_db)
):
    """List all registered services"""
    query = select(ServiceRegistry)
    if not include_inactive:
        query = query.where(ServiceRegistry.is_active == True)
    
    services = db.exec(query.offset(skip).limit(limit)).all()
    return services

@router.get("/{service_name}", response_model=ServiceResponse)
async def get_service(
    service_name: str,
    current_user: TokenData = Depends(PermissionChecker("auth", "service", "read")),
    db: Session = Depends(get_db)
):
    """Get service details by name"""
    service = db.exec(
        select(ServiceRegistry).where(ServiceRegistry.service_name == service_name)
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found"
        )
    
    return service

@router.put("/{service_name}", response_model=ServiceResponse)
async def update_service(
    service_name: str,
    display_name: Optional[str] = Body(None),
    resource_types: Optional[List[str]] = Body(None),
    actions: Optional[List[str]] = Body(None),
    base_url: Optional[str] = Body(None),
    description: Optional[str] = Body(None),
    is_active: Optional[bool] = Body(None),
    current_user: TokenData = Depends(PermissionChecker("auth", "service", "update")),
    db: Session = Depends(get_db)
):
    """Update service configuration"""
    service = db.exec(
        select(ServiceRegistry).where(ServiceRegistry.service_name == service_name)
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found"
        )
    
    # Update fields
    if display_name is not None:
        service.display_name = display_name
    if resource_types is not None:
        service.resource_types = resource_types
    if actions is not None:
        service.available_actions = actions
    if base_url is not None:
        service.base_url = base_url
    if description is not None:
        service.description = description
    if is_active is not None:
        service.is_active = is_active
    
    service.updated_at = datetime.utcnow()
    db.add(service)
    db.commit()
    db.refresh(service)
    
    return service

@router.delete("/{service_name}")
async def deactivate_service(
    service_name: str,
    permanent: bool = False,
    current_user: TokenData = Depends(PermissionChecker("auth", "service", "delete")),
    db: Session = Depends(get_db)
):
    """Deactivate or permanently delete a service"""
    service = db.exec(
        select(ServiceRegistry).where(ServiceRegistry.service_name == service_name)
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found"
        )
    
    if permanent:
        # Permanent deletion (only for development/testing)
        db.delete(service)
        db.commit()
        return {"message": f"Service '{service_name}' permanently deleted"}
    else:
        # Soft delete - just deactivate
        service.is_active = False
        service.updated_at = datetime.utcnow()
        db.add(service)
        db.commit()
        return {"message": f"Service '{service_name}' deactivated"}

@router.post("/{service_name}/reactivate")
async def reactivate_service(
    service_name: str,
    current_user: TokenData = Depends(PermissionChecker("auth", "service", "update")),
    db: Session = Depends(get_db)
):
    """Reactivate a deactivated service"""
    service = db.exec(
        select(ServiceRegistry).where(ServiceRegistry.service_name == service_name)
    ).first()
    
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_name}' not found"
        )
    
    service.is_active = True
    service.updated_at = datetime.utcnow()
    db.add(service)
    db.commit()
    
    return {"message": f"Service '{service_name}' reactivated"}
# teachverse_auth/dependencies/auth.py
from typing import Optional, List
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlmodel import Session, select
from datetime import datetime
import jwt
from jwt.exceptions import InvalidTokenError

from ..core.database import get_db
from ..core.config import settings
from ..core.security import get_token_from_request
from ..models.user import User
from ..models.permission import ServiceRegistry
from ..services.permission_service import PermissionService
from ..core.exceptions import UserNotFoundError, UserInactiveError

# Global OAuth2 scheme (will be initialized)
oauth2_scheme: Optional[OAuth2PasswordBearer] = None

def init_oauth2(db: Session) -> OAuth2PasswordBearer:
    """Initialize OAuth2 scheme with dynamic scopes from service registry"""
    global oauth2_scheme
    
    # Build scopes dynamically
    scopes = {}
    
    # Get all registered services
    services = db.exec(select(ServiceRegistry)).all()
    
    for service in services:
        for resource_type in service.resource_types:
            for action in service.available_actions:
                scope_name = f"{service.service_name}:{resource_type}:{action}"
                scope_description = f"{action} any {resource_type} in {service.service_name} service"
                scopes[scope_name] = scope_description
            
            # Add wildcard scope for all actions on this resource
            scope_name = f"{service.service_name}:{resource_type}:*"
            scope_description = f"all actions on any {resource_type} in {service.service_name} service"
            scopes[scope_name] = scope_description
        
        # Add service-level wildcard
        scope_name = f"{service.service_name}:*:*"
        scope_description = f"all actions on all resources in {service.service_name} service"
        scopes[scope_name] = scope_description
    
    # Add admin scope
    scopes["admin"] = "Full administrative access"
    
    oauth2_scheme = OAuth2PasswordBearer(
        tokenUrl=f"{settings.API_PREFIX}/auth/token",
        scopes=scopes
    )
    
    return oauth2_scheme

async def get_oauth2_scheme_dependency(
    request: Request, 
    db: Session = Depends(get_db)
) -> OAuth2PasswordBearer:
    """Ensure oauth2_scheme is initialized"""
    global oauth2_scheme
    if oauth2_scheme is None:
        oauth2_scheme = init_oauth2(db)
    return oauth2_scheme

class TokenData:
    def __init__(self, sub: str, scopes: List[str] = None, user_data: dict = None):
        self.sub = sub
        self.scopes = scopes or []
        self.user_data = user_data or {}

async def get_current_user(
    security_scopes: SecurityScopes,
    request: Request,
    db: Session = Depends(get_db)
) -> TokenData:
    """Get current user with dynamic scope validation"""
    token = get_token_from_request(request)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != "access":
            raise credentials_exception
        
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        token_scopes = payload.get("scopes", [])
        token_data = TokenData(
            sub=user_id,
            scopes=token_scopes,
            user_data={
                "email": payload.get("email"),
                "role": payload.get("role"),
                "organization_id": payload.get("organization_id"),
                "name": payload.get("name"),
            }
        )
        
    except InvalidTokenError:
        raise credentials_exception
    
    user = db.get(User, int(user_id))
    if not user:
        raise UserNotFoundError()
    
    if user.status != "active":
        raise UserInactiveError()
    
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )
    
    return token_data

async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[TokenData]:
    """Optional authentication - returns None if no valid token"""
    token = get_token_from_request(request)
    if not token:
        return None
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != "access":
            return None
        
        return TokenData(
            sub=payload.get("sub"),
            scopes=payload.get("scopes", []),
            user_data={
                "email": payload.get("email"),
                "role": payload.get("role"),
                "organization_id": payload.get("organization_id"),
            }
        )
    except (InvalidTokenError, Exception):
        return None

def require_permission(service: str, resource_type: str, action: str):
    """Require specific permission on any resource"""
    async def dependency(
        current_user: TokenData = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        has_perm = await PermissionService.check_permission(
            db=db,
            user_id=int(current_user.sub),
            service=service,
            resource_type=resource_type,
            resource_id="*",
            action=action
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {service}:{resource_type}:*:{action}"
            )
        return current_user
    return Depends(dependency)

def require_resource_permission(service: str, resource_type: str, resource_id: str, action: str):
    """Require permission on a specific resource"""
    async def dependency(
        current_user: TokenData = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        has_perm = await PermissionService.check_permission(
            db=db,
            user_id=int(current_user.sub),
            service=service,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action
        )
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission on resource: {resource_id}"
            )
        return current_user
    return Depends(dependency)

def require_role(required_role: str):
    """Require specific role"""
    async def dependency(
        current_user: TokenData = Depends(get_current_user)
    ):
        if current_user.user_data.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {required_role}"
            )
        return current_user
    return Depends(dependency)
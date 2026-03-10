# teachverse_auth/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta, datetime
import jwt
from ..core.database import get_db
from ..core.config import settings
from ..core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    Token,
    RefreshToken,
)
from ..models.user import User
from ..models.permission import ServiceRegistry
from ..services.permission_service import PermissionService
from ..dependencies.auth import get_oauth2_scheme_dependency, get_current_user

router = APIRouter(prefix=f"{settings.API_PREFIX}/auth", tags=["authentication"])

@router.post("/token", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 compatible token login with dynamic scopes"""
    
    # Initialize OAuth2 scheme (this will build scopes)
    oauth2_scheme = await get_oauth2_scheme_dependency(request, db)
    
    # Find user
    user = db.exec(
        select(User).where(User.email == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Get user permissions to determine scopes
    permissions = await PermissionService.get_user_permissions(db, user.id)
    
    # Parse requested scopes
    requested_scopes = form_data.scopes.split() if form_data.scopes else []
    
    # Filter to only scopes the user actually has
    granted_scopes = [s for s in requested_scopes if s in permissions]
    
    # If no scopes requested, grant default read scope
    if not granted_scopes and permissions:
        # Grant first available scope or default
        granted_scopes = [p for p in permissions if p.endswith(":read")][:1] or [permissions[0]]
    
    # Create tokens
    access_token = create_access_token(
        data={
            "id": user.id,
            "email": user.email,
            "role": user.role.value,
            "organization_id": user.organization_id,
            "name": user.full_name,
        },
        scopes=granted_scopes
    )
    
    refresh_token = create_refresh_token(
        data={"id": user.id}
    )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.add(user)
    db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_data: RefreshToken,
    db: Session = Depends(get_db)
):
    """Get new access token using refresh token"""
    try:
        payload = jwt.decode(
            refresh_data.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        user_id = int(payload.get("sub"))
        user = db.get(User, user_id)
        
        if not user or user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Get permissions for new token
        permissions = await PermissionService.get_user_permissions(db, user_id)
        
        # Create new tokens
        access_token = create_access_token(
            data={
                "id": user.id,
                "email": user.email,
                "role": user.role.value,
                "organization_id": user.organization_id,
                "name": user.full_name,
            },
            scopes=permissions
        )
        
        new_refresh_token = create_refresh_token(
            data={"id": user.id}
        )
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/scopes")
async def get_available_scopes(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all available scopes from registered services"""
    
    services = db.exec(select(ServiceRegistry)).all()
    scopes = {}
    
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
    
    scopes["admin"] = "Full administrative access"
    
    return {"scopes": scopes}

@router.get("/me")
async def read_users_me(
    current_user = Depends(get_current_user)
):
    """Get current user information"""
    return {
        "user_id": current_user.sub,
        "email": current_user.user_data.get("email"),
        "role": current_user.user_data.get("role"),
        "organization_id": current_user.user_data.get("organization_id"),
        "name": current_user.user_data.get("name"),
        "scopes": current_user.scopes,
    }

@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user)
):
    """Logout user (client should discard tokens)"""
    # In production, you could blacklist the token here
    return {"message": "Successfully logged out"}

@router.post("/register")
async def register(
    email: str,
    password: str,
    full_name: str,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Check if user exists
    existing = db.exec(
        select(User).where(User.email == email)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    from ..core.security import get_password_hash
    user = User(
        email=email,
        full_name=full_name,
        password_hash=get_password_hash(password),
        status="pending"
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message": "User created successfully", "user_id": user.id}
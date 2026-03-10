from datetime import datetime, timedelta, timezone
from typing import Optional, List, Union, Any
import secrets
import hashlib
import hmac

import jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel, ValidationError
from sqlmodel import Session

from ..core.config import settings
from ..core.database import get_db
from ..models.user import User
from ..services.permission_service import PermissionService

# Modern password hashing with pwdlib (supports multiple algorithms)
password_hash = PasswordHash.recommended()

# OAuth2 scheme with scopes
oauth2_scheme = None 
def get_token_from_request(request: Request) -> Optional[str]:
    """Extract token from request for dynamic OAuth2"""
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except:
        return None

# ========== Pydantic Models ==========

class TokenData(BaseModel):
    """Token payload data"""
    sub: Union[str, int]
    exp: datetime
    scopes: List[str] = []
    user_data: dict = {}

class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshToken(BaseModel):
    """Refresh token request"""
    refresh_token: str

class UserInDB(BaseModel):
    """User model for token creation"""
    id: int
    email: str
    role: str
    organization_id: Optional[int] = None
    full_name: str

# ========== Core Security Functions ==========

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using modern pwdlib"""
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password using modern pwdlib (supports bcrypt, argon2, etc.)"""
    return password_hash.hash(password)

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
    scopes: List[str] = None
) -> str:
    """Create JWT access token with scopes"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "sub": str(data.get("id", data.get("sub"))),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "scopes": scopes or []
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Create refresh token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "sub": str(data.get("id", data.get("sub"))),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_token(token: str, expected_type: Optional[str] = "access") -> dict:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        if expected_type and payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}"
            )
        
        return payload
        
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

# ========== API Key Functions ==========
def generate_secure_key(length: int = 32) -> str:
    """Generate a cryptographically secure random key"""
    return secrets.token_urlsafe(length)

def generate_api_key() -> str:
    """Generate API key for services"""
    return f"tvk_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    salt = secrets.token_hex(16)
    return f"{salt}:{hashlib.sha256(f'{salt}{api_key}'.encode()).hexdigest()}"

def verify_api_key(api_key: str, hashed: str) -> bool:
    """Verify API key against stored hash"""
    try:
        salt, hash_value = hashed.split(":")
        return hmac.compare_digest(
            hashlib.sha256(f"{salt}{api_key}".encode()).hexdigest(),
            hash_value
        )
    except:
        return False
    
# ========== FastAPI Dependencies ==========
async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> TokenData:
    """
    Get current user from token with scope validation
    This is the main authentication dependency
    """
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
        # Decode token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Validate token type
        if payload.get("type") != "access":
            raise credentials_exception
        
        # Extract user data
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        token_scopes = payload.get("scopes", [])
        
        # Create token data
        token_data = TokenData(
            sub=user_id,
            exp=datetime.fromtimestamp(payload.get("exp")),
            scopes=token_scopes,
            user_data={
                "email": payload.get("email"),
                "role": payload.get("role"),
                "organization_id": payload.get("organization_id"),
                "name": payload.get("name"),
            }
        )
        
    except (InvalidTokenError, ValidationError) as e:
        raise credentials_exception
    
    # Verify user exists in database
    user = db.get(User, int(user_id))
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Check required scopes
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {scope}",
                headers={"WWW-Authenticate": authenticate_value},
            )
    
    return token_data

async def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[TokenData]:
    """Optional authentication - returns None if no valid token"""
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
            exp=datetime.fromtimestamp(payload.get("exp")),
            scopes=payload.get("scopes", []),
            user_data={
                "email": payload.get("email"),
                "role": payload.get("role"),
                "organization_id": payload.get("organization_id"),
            }
        )
    except (InvalidTokenError, ValidationError):
        return None

# ========== Permission Dependencies ==========

def require_permission(service: str, resource_type: str, action: str):
    """Require a specific permission on any resource"""
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

def require_any_permission(permissions: List[str]):
    """Require any of the specified permissions"""
    async def dependency(
        current_user: TokenData = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        for perm in permissions:
            service, resource_type, resource_id, action = perm.split(":", 3)
            has_perm = await PermissionService.check_permission(
                db=db,
                user_id=int(current_user.sub),
                service=service,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action
            )
            if has_perm:
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Need at least one of: {', '.join(permissions)}"
        )
    return Depends(dependency)

def require_all_permissions(permissions: List[str]):
    """Require all specified permissions"""
    async def dependency(
        current_user: TokenData = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        for perm in permissions:
            service, resource_type, resource_id, action = perm.split(":", 3)
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
                    detail=f"Missing permission: {perm}"
                )
        return current_user
    return Depends(dependency)
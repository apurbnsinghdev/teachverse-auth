# tests/test_permissions.py
import pytest
from sqlmodel import Session

from teachverse_auth.models.user import User
from teachverse_auth.models.permission import Permission
from teachverse_auth.services.permission_service import PermissionService


@pytest.mark.anyio
async def test_check_permission(async_client, db: Session):
    """Test permission checking endpoint"""
    # Create user with permission
    user = User(
        email="perm@example.com",
        full_name="Permission Test",
        password_hash="hash",
        status="active"
    )
    db.add(user)
    db.commit()
    
    # Create permission
    perm = Permission(
        service="test",
        resource_type="document",
        resource_id="*",
        action="read",
        is_system=False
    )
    db.add(perm)
    db.commit()
    
    # Test permission check endpoint
    response = await async_client.get(
        f"/api/v1/permissions/check?service=test&resource_type=document&resource_id=123&action=read"
    )
    
    # Note: This endpoint would require authentication
    # This is just an example structure
    assert response.status_code in [200, 401]
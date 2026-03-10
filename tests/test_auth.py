# tests/test_auth.py
import pytest
from sqlmodel import Session

from teachverse_auth.core.security import get_password_hash
from teachverse_auth.models.user import User


@pytest.mark.anyio
async def test_login(async_client, db: Session):
    """Test login endpoint"""
    # Create test user
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=get_password_hash("password123"),
        status="active"
    )
    db.add(user)
    db.commit()
    
    # Test login
    response = await async_client.post(
        "/api/v1/auth/token",
        data={
            "username": "test@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_wrong_password(async_client, db: Session):
    """Test login with wrong password"""
    user = User(
        email="test2@example.com",
        full_name="Test User 2",
        password_hash=get_password_hash("password123"),
        status="active"
    )
    db.add(user)
    db.commit()
    
    response = await async_client.post(
        "/api/v1/auth/token",
        data={
            "username": "test2@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
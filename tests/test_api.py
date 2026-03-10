# tests/test_api.py
import pytest
from httpx import ASGITransport, AsyncClient

from teachverse_auth.main import app


@pytest.mark.anyio
async def test_health_endpoint(async_client):
    """Test health endpoint with async client"""
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.anyio
async def test_login_endpoint(async_client, db):
    """Test login endpoint"""
    # First create a user (sync or async)
    from teachverse_auth.core.security import get_password_hash
    from teachverse_auth.models.user import User
    
    user = User(
        email="test@example.com",
        full_name="Test User",
        password_hash=get_password_hash("password123"),
        status="active"
    )
    db.add(user)
    db.commit()
    
    # Test login
    async with AsyncClient(
        transport=ASGITransport(app=app), 
        base_url="http://test"
    ) as ac:
        response = await ac.post(
            "/api/v1/auth/token",
            data={
                "username": "test@example.com",
                "password": "password123"
            }
        )
    assert response.status_code == 200
    assert "access_token" in response.json()
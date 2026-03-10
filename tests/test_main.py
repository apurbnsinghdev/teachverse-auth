# tests/test_main.py
import pytest
from httpx import ASGITransport, AsyncClient

from teachverse_auth.main import app


@pytest.mark.anyio
async def test_health_endpoint():
    """Test health endpoint with anyio"""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        response = await ac.get("/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "auth"}
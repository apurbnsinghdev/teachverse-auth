# tests/test_services.py
import pytest
from sqlmodel import Session, select

from teachverse_auth.models.permission import ServiceRegistry
from teachverse_auth.services.permission_service import PermissionService


@pytest.mark.anyio
async def test_register_service(db: Session):
    """Test service registration"""
    service = await PermissionService.register_service(
        db=db,
        service_name="anyio_test",
        display_name="AnyIO Test Service",
        resource_types=["item", "collection"],
        actions=["create", "read", "update"],
        base_url="http://anyio-test:8000"
    )
    
    assert service.id is not None
    assert service.service_name == "anyio_test"
    assert service.display_name == "AnyIO Test Service"
    assert service.resource_types == ["item", "collection"]
    assert service.available_actions == ["create", "read", "update"]


@pytest.mark.anyio
async def test_list_services(async_client):
    """Test listing services via API"""
    response = await async_client.get("/api/v1/services/")
    
    # This would require authentication in real app
    # Just showing the pattern
    assert response.status_code in [200, 401]
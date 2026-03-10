# tests/conftest.py
import pytest
from sqlmodel import SQLModel, Session, create_engine
from httpx import ASGITransport, AsyncClient
from typing import AsyncGenerator, Generator

from teachverse_auth.main import app
from teachverse_auth.core.database import get_db
from teachverse_auth.data.defaults import DEFAULT_SERVICES
from teachverse_auth.services.permission_service import PermissionService

# ===== SESSION SCOPED =====
# Created ONCE for all tests
@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    engine = create_engine(
        "sqlite:///./test.db",
        connect_args={"check_same_thread": False},
        echo=False
    )
    SQLModel.metadata.create_all(engine)
    return engine

# Created once per test module
@pytest.fixture(scope="module")    
def module_data():
    return {"shared": "data"}

# Created fresh for EACH test (default)
@pytest.fixture(scope="function")  
def db_session(engine):
    session = Session(engine)
    yield session
    session.close()  # Clean up after each test
    
# This runs FIRST (autouse) - sets up the playground
#The autouse=True means: "Run this fixture automatically for ALL tests without being explicitly requested!".
@pytest.fixture(scope="session", autouse=True)
async def setup_test_services():
    """Setup default services for testing - runs automatically"""
    engine = create_engine("sqlite:///./test.db")
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as db:
        for service in DEFAULT_SERVICES:
            await PermissionService.register_service(
                db=db,
                service_name=service["name"],
                display_name=service["display_name"],
                resource_types=service["resource_types"],
                actions=service["actions"]
            )
    
    return engine # Not even used, but could be

# ===== FUNCTION SCOPED (default) =====
# This runs SECOND - provides database sessions to tests
@pytest.fixture
def db(test_engine) -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session # Test runs here
    
    # Cleanup after test
    session.close()
    transaction.rollback()
    connection.close()

# ===== ASYNC FIXTURE =====
@pytest.fixture
async def async_client(db) -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client - using AnyIO pattern"""
    # Override database dependency
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create client
    async with AsyncClient(
        transport=ASGITransport(app=app), # This creates a direct connection to our app WITHOUT HTTP
        base_url="http://test"
    ) as client:
        yield client

    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
def client(db):
    """Keep sync client for backward compatibility"""
    from fastapi.testclient import TestClient
    
    def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
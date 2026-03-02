"""Main FastAPI application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import (
    auth,
    users,
    roles,
    permissions,
    services,
    admin
)
from .core.config import settings

def create_app() -> FastAPI:
    """Application factory"""
    app = FastAPI(
        title="TEACHVERSE Auth Service",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(roles.router)
    app.include_router(permissions.router)
    app.include_router(services.router)
    app.include_router(admin.router)

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "auth"}

    return app

app = create_app()
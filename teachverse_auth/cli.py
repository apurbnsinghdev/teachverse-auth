#!/usr/bin/env python3
"""CLI commands for TEACHVERSE Auth"""
import typer
import uvicorn
import subprocess
import sys
from typing import Optional
from sqlmodel import Session, select
from datetime import datetime

from .core.database import engine, init_db
from .core.security import get_password_hash
from .models.user import User
from .models.permission import ServiceRegistry
from .services.permission_service import PermissionService
from .data.defaults import DEFAULT_SERVICES

app = typer.Typer(help="TEACHVERSE Auth CLI")


@app.command()
def setup():
    """Interactive setup wizard - creates .env and initializes everything"""
    print("\n" + "="*60)
    print("🔧 **TEACHVERSE Auth Setup Wizard**")
    print("="*60)
    
    # This will trigger the .env creation in config.py
    from .core.config import Settings
    Settings()
    
    # Now run migrations
    print("\n📦 Running database migrations...")
    migrate()
    
    # Initialize default services
    print("\n📦 Initializing default services...")
    init_services()
    
    print("\n✅ Setup complete!")
    print("\nNext steps:")
    print("  1. Create admin:     teachverse-auth createsuperuser")
    print("  2. Start server:     teachverse-auth runserver")
    print("  3. View docs:        http://localhost:8000/api/docs\n")
    
@app.command()
def migrate():
    """Initialize database tables"""
    try:
        init_db()
        typer.echo("✅ Database tables created successfully!")
    except Exception as e:
        typer.echo(f"❌ Migration failed: {e}")
        raise typer.Exit(1)

@app.command()
def createsuperuser(
    email: str = typer.Option(..., prompt=True),
    full_name: str = typer.Option(..., prompt=True),
    password: str = typer.Option(..., prompt=True, hide_input=True, confirmation_prompt=True),
):
    """Create a superuser"""
    with Session(engine) as db:
        existing = db.exec(select(User).where(User.email == email)).first()
        if existing:
            typer.echo(f"❌ User with email {email} already exists!")
            raise typer.Exit(1)
        
        user = User(
            email=email,
            full_name=full_name,
            password_hash=get_password_hash(password),
            role="platform_admin",
            status="active",
            is_email_verified=True,
        )
        
        db.add(user)
        db.commit()
        
        typer.echo(f"✅ Superuser {email} created successfully!")

@app.command()
def init_services():
    """Initialize default services and permissions"""
    with Session(engine) as db:
        for service in DEFAULT_SERVICES:
            PermissionService.register_service(
                db=db,
                service_name=service["name"],
                display_name=service["display_name"],
                resource_types=service["resource_types"],
                actions=service["actions"]
            )
        
        typer.echo(f"✅ Registered {len(DEFAULT_SERVICES)} services")

@app.command()
def runserver(
    host: str = typer.Option("127.0.0.1", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    reload: bool = typer.Option(False, "--reload", "-r"),
):
    """Run the development server"""
    typer.echo(f"🚀 Starting TEACHVERSE Auth server at http://{host}:{port}")
    uvicorn.run(
        "teachverse_auth.main:app",
        host=host,
        port=port,
        reload=reload
    )

def main():
    app()

if __name__ == "__main__":
    main()
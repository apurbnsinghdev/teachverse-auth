# teachverse_auth/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Dict, Any, ClassVar
import os
from pathlib import Path
import secrets
from datetime import datetime

class Settings(BaseSettings):
    """Application settings - auto-creates .env on first run"""
    
    APP_NAME: str = "TEACHVERSE Auth"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    DATABASE_URL: Optional[str] = Field(None, description="PostgreSQL connection string")
    SECRET_KEY: Optional[str] = Field(None, description="JWT signing key")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: Optional[str] = Field(None, description="Redis URL for token blacklisting")
    
    extra_config: Dict[str, Any] = Field(default={})
    _loaded_services: ClassVar[set] = set()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"
    
    def __init__(self, **kwargs):
        env_path = Path(".env")
        if not env_path.exists():
            self._run_interactive_setup()
        super().__init__(**kwargs)
    
    def _run_interactive_setup(self):
        """Run interactive setup to create .env file"""
        print("\n🔧 **First Time Setup - Creating Configuration**")
        print("=" * 50)
        
        secret_key = secrets.token_urlsafe(32)
        
        print("\n📦 **Database Configuration**")
        print("Examples:")
        print("  • Local:  postgresql://username@localhost:5432/teachverse")
        print("  • Docker: postgresql://postgres:postgres@localhost:5432/teachverse")
        
        db_url = input("\nEnter DATABASE_URL: ").strip()
        while not db_url:
            print("❌ Database URL cannot be empty!")
            db_url = input("Enter DATABASE_URL: ").strip()
        
        print("\n📦 **Redis Configuration (Optional)**")
        redis_url = input("Enter REDIS_URL (or press Enter to skip): ").strip()
        
        env_content = f"""# =============================================
# TEACHVERSE Auth - Auto-generated Configuration
# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# =============================================

# ---------- Core Database ----------
DATABASE_URL={db_url}

# ---------- Security ----------
SECRET_KEY={secret_key}
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ---------- Redis (Optional) ----------
"""
        env_content += f"REDIS_URL={redis_url}\n" if redis_url else "# REDIS_URL=redis://localhost:6379/0\n"
        
        env_content += """
# ---------- API Settings ----------
API_PREFIX=/api/v1
DEBUG=false
"""
        
        env_path = Path(".env")
        env_path.write_text(env_content)
        
        print("\n✅ **.env file created successfully!**")
        print(f"📁 Location: {env_path.absolute()}")
        
        cont = input("\nRun migrations now? (y/n): ").strip().lower()
        if cont == 'y':
            import subprocess
            import sys
            result = subprocess.run([sys.executable, "-m", "teachverse_auth.cli", "migrate"])
            if result.returncode == 0:
                print("✅ Database setup complete!")
                
                create_admin = input("\n👤 Create a superuser now? (y/n): ").strip().lower()
                if create_admin == 'y':
                    subprocess.run([sys.executable, "-m", "teachverse_auth.cli", "createsuperuser"])

settings = Settings()
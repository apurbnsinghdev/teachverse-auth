# tests/test_config.py
import pytest
import os
from teachverse_auth.core.config import Settings

def test_settings_load_defaults():
    """Verify that settings load with default values when no .env exists."""
    settings = Settings()
    assert settings.APP_NAME == "TEACHVERSE Auth"
    assert settings.ALGORITHM == "HS256"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 30

def test_settings_override_via_env(monkeypatch):
    """Verify that environment variables correctly override defaults."""
    # Simulate setting an environment variable
    monkeypatch.setenv("APP_NAME", "TEST_APP")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    
    settings = Settings()
    assert settings.APP_NAME == "TEST_APP"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
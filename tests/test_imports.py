# tests/test_imports.py
def test_imports():
    """Test that all modules can be imported without errors"""
    try:
        from teachverse_auth.api import auth, users, roles, permissions, services, admin
        from teachverse_auth.dependencies import auth as deps
        from teachverse_auth.core import security, config, database
        from teachverse_auth.models import user, role, permission, organization
        assert True
    except Exception as e:
        assert False, f"Import failed: {e}"
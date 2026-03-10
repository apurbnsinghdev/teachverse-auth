# tests/test_cli.py
from typer.testing import CliRunner
from teachverse_auth.cli import app

runner = CliRunner()

def test_createsuperuser_command_success():
    """Test creating a superuser via CLI with mocked input."""
    # Inputs: email, full_name, password, confirm_password
    input_data = "admin@teachverse.com\nAdmin User\nsecurePassword123\nsecurePassword123\n"
    
    result = runner.invoke(app, ["createsuperuser"], input=input_data)
    
    assert result.exit_code == 0
    assert "✅ Superuser admin@teachverse.com created successfully!" in result.stdout

def test_createsuperuser_duplicate_email():
    """Test that creating a user with an existing email fails gracefully."""
    # First creation
    input_data = "duplicate@teachverse.com\nUser\npass123\npass123\n"
    runner.invoke(app, ["createsuperuser"], input=input_data)
    
    # Second creation (should trigger the 'already exists' error)
    result = runner.invoke(app, ["createsuperuser"], input=input_data)
    
    assert result.exit_code == 1
    assert "❌ User with email duplicate@teachverse.com already exists!" in result.stdout
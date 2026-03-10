# Contributing to TeachVerse Auth

Thank you for your interest in contributing! We aim to keep this package production-ready, highly tested, and easy to maintain. Please follow these guidelines to help us keep the quality high.

## 🛠 Getting Started
1. **Fork and Clone** the repository.
2. **Setup your environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -e ".[test]"
    ```
3. **Verify installation**:
Run the test suite to ensure everything is working correctly on your machine:
```Bash
pytest tests/ -v
```

# 🏗 Development Workflow
We follow a "Security-First" development approach.

1. New Features
Keep it modular: New features should live in src/teachverse_auth/.

Add Tests: Every new feature or fix must include a corresponding test in the tests/ directory.

Update CLI: If your feature impacts setup or initialization, update src/teachverse_auth/cli.py and the corresponding tests.

2. Testing
Before submitting a Pull Request, ensure your code passes all checks:

Run Unit/Integration Tests: pytest tests/

Check Coverage:

```Bash
pytest --cov=teachverse_auth tests/
```
3. Pull Request Process
Branching: Use descriptive branch names (e.g., feature/redis-caching, fix/permission-resolution).

Documentation: If you add a new API endpoint or dependency, update the relevant file in docs/.

Review: All PRs must pass the CI pipeline (if configured) and be reviewed by at least one maintainer.

🛡 Security
This is an authentication/authorization package. Security is our top priority.

Never hardcode secrets. Use environment variables.

Ensure any changes to the PermissionResolver or PermissionChecker are heavily unit-tested.

If you find a security vulnerability, please report it via private communication rather than creating a public issue.